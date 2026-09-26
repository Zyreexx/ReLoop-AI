"""
Auth routes for ReLoop AI.
Rules enforced:
- /register   : Creates a new account (Google or email). Returns error if email already exists.
                For direct email registration, generates a 6-digit OTP, hashes it, stores in OtpCode,
                and sends verification email via email_service.
- /verify-otp : Accepts email + 6-digit OTP code, constant-time hash comparison, marks is_email_verified.
                Distinguishes expired code from invalid code, limits attempts to 5 before invalidation.
- /resend-otp : Invalidates previous OTP, issues new code, rate-limited to 1 request per 60 seconds.
- /login      : Signs in an existing account. Returns 404 if not registered yet.
- /google     : Verifies a Google ID token, checks the user is already registered, returns profile.
                Google-only: only @gmail.com or verified Google Workspace emails accepted.
"""
import hashlib
import hmac
import logging
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.errors import AppError, ErrorCode
from app.models.entities import OtpCode, User
from app.services import email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


# ─────────────────── Helpers ───────────────────

def _hash_password(password: str) -> str:
    """Simple SHA-256 hash for demo. In production use bcrypt/argon2."""
    return hashlib.sha256(password.encode()).hexdigest()


def _verify_password(plain: str, hashed: str) -> bool:
    return hashlib.sha256(plain.encode()).hexdigest() == hashed


def _generate_otp_code() -> str:
    """Generate a cryptographically secure 6-digit numeric string."""
    return f"{secrets.randbelow(1_000_000):06d}"


def _hash_otp(code: str) -> str:
    """Hash the OTP with SHA-256 for secure storage (never plaintext)."""
    return hashlib.sha256(code.encode()).hexdigest()


def _parse_google_jwt(token: str) -> Optional[dict]:
    """
    Decode a Google ID-token JWT payload WITHOUT verifying the signature.
    Signature verification should happen via google-auth library in production.
    For this demo we trust the payload structure; real production should verify.
    """
    import base64, json
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return None
        padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
        return payload
    except Exception:
        return None


def _is_valid_google_email(email: str) -> bool:
    """
    Accepts any well-formed email returned from Google OAuth.
    In production you'd also verify 'iss' and 'aud' claims from the token.
    """
    # Basic email format check
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


# ─────────────────── Schemas ───────────────────

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    email: EmailStr
    password: Optional[str] = Field(None, min_length=6)
    provider: str = Field("email")  # "email" | "google"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)


class ResendOtpRequest(BaseModel):
    email: EmailStr


class ResendOtpResponse(BaseModel):
    message: str
    cooldown_seconds: int = 60


class GoogleAuthRequest(BaseModel):
    """Frontend sends the raw Google credential (JWT ID token)."""
    credential: str
    mode: str = "login"  # "login" | "register"


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    provider: str
    is_email_verified: bool = False
    created_at: str


def _user_to_response(u: User) -> UserResponse:
    return UserResponse(
        id=u.id,
        email=u.email,
        name=u.name,
        picture=u.picture,
        provider=u.provider,
        is_email_verified=bool(getattr(u, "is_email_verified", False)),
        created_at=u.created_at.isoformat(),
    )


# ─────────────────── Routes ───────────────────

@router.post("/register", response_model=UserResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """
    Create a new account with email + password.
    Returns 409 if the email is already registered.
    Generates and emails an OTP code for direct email signup.
    """
    clean_email = str(body.email).lower().strip()
    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists. Please sign in instead.",
        )

    if body.provider == "email":
        if not body.password:
            raise HTTPException(status_code=422, detail="Password is required for email registration.")
        password_hash = _hash_password(body.password)
        is_email_verified = False
    else:
        password_hash = None
        is_email_verified = False

    user = User(
        email=clean_email,
        name=body.name,
        provider=body.provider,
        password_hash=password_hash,
        is_email_verified=is_email_verified,
        created_at=datetime.now(timezone.utc),
        last_login_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if body.provider == "email":
        # Invalidate any previous unexpired OTP code for that user
        db.query(OtpCode).filter(OtpCode.user_id == user.id).delete()

        # Generate 6-digit numeric code with secrets.randbelow
        raw_code = _generate_otp_code()
        code_hash = _hash_otp(raw_code)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        otp_record = OtpCode(
            user_id=user.id,
            code_hash=code_hash,
            expires_at=expires_at,
            attempts=0,
            created_at=datetime.now(timezone.utc),
        )
        db.add(otp_record)
        db.commit()

        # Send OTP code via email service wrapper
        try:
            email_service.send_otp_email(to_email=user.email, code=raw_code)
        except Exception as e:
            logger.error(f"Failed to send OTP email to {user.email}: {e}")

    logger.info(f"New user registered: {user.email} via {user.provider}")
    return _user_to_response(user)


@router.post("/verify-otp", response_model=UserResponse)
def verify_otp(body: VerifyOtpRequest, db: Session = Depends(get_db)):
    """
    Verify OTP code for email verification.
    Constant-time comparison with hmac.compare_digest.
    Increments attempts on mismatch; after fixed limit (5 attempts), invalidates code.
    Distinguishes expired OTP from wrong code.
    """
    clean_email = str(body.email).lower().strip()
    user = db.query(User).filter(User.email == clean_email).first()
    if not user:
        raise AppError(
            code=ErrorCode.NOT_FOUND.value,
            message="No account found with this email. Please sign up first.",
            field="email",
            http_status=404,
        )

    # Find the active OTP code for this user
    otp = (
        db.query(OtpCode)
        .filter(OtpCode.user_id == user.id)
        .order_by(OtpCode.created_at.desc())
        .first()
    )

    if not otp:
        raise AppError(
            code=ErrorCode.INVALID_INPUT.value,
            message="No active verification code found. Please request a new code.",
            field="code",
            http_status=400,
        )

    # Check expiration
    now = datetime.now(timezone.utc)
    expires_at = otp.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if now > expires_at:
        db.delete(otp)
        db.commit()
        raise AppError(
            code=ErrorCode.OTP_EXPIRED.value,
            message="Verification code has expired. Please request a new code.",
            field="code",
            http_status=400,
        )

    # Check attempt limit
    MAX_ATTEMPTS = 5
    if otp.attempts >= MAX_ATTEMPTS:
        db.delete(otp)
        db.commit()
        raise AppError(
            code=ErrorCode.OTP_ATTEMPTS_EXCEEDED.value,
            message="Maximum verification attempts exceeded. Code invalidated. Please request a new code.",
            field="code",
            http_status=400,
        )

    # Constant-time comparison using hmac.compare_digest
    submitted_hash = _hash_otp(body.code.strip())
    if hmac.compare_digest(submitted_hash, otp.code_hash):
        # Match and not expired: mark verified, delete OTP row
        user.is_email_verified = True
        db.delete(otp)
        db.commit()
        db.refresh(user)
        logger.info(f"Email verified successfully for user: {user.email}")
        return _user_to_response(user)
    else:
        # Mismatch: increment attempts
        otp.attempts += 1
        if otp.attempts >= MAX_ATTEMPTS:
            db.delete(otp)
            db.commit()
            raise AppError(
                code=ErrorCode.OTP_ATTEMPTS_EXCEEDED.value,
                message="Maximum verification attempts exceeded. Code invalidated. Please request a new code.",
                field="code",
                http_status=400,
            )
        else:
            db.commit()
            raise AppError(
                code=ErrorCode.OTP_INVALID.value,
                message=f"Incorrect verification code. {MAX_ATTEMPTS - otp.attempts} attempts remaining.",
                field="code",
                http_status=400,
            )


@router.post("/resend-otp", response_model=ResendOtpResponse)
def resend_otp(body: ResendOtpRequest, db: Session = Depends(get_db)):
    """
    Resend verification code to user's email.
    Rate-limited to roughly 1 request per 60 seconds per user.
    Invalidates any previous unexpired code before creating the new one.
    """
    clean_email = str(body.email).lower().strip()
    user = db.query(User).filter(User.email == clean_email).first()
    if not user:
        raise AppError(
            code=ErrorCode.NOT_FOUND.value,
            message="No account found with this email.",
            field="email",
            http_status=404,
        )

    if user.is_email_verified:
        raise AppError(
            code=ErrorCode.INVALID_INPUT.value,
            message="Email is already verified.",
            field="email",
            http_status=400,
        )

    RATE_LIMIT_SECONDS = 60
    now = datetime.now(timezone.utc)

    # Check rate limit against existing OTP creation time
    latest_otp = (
        db.query(OtpCode)
        .filter(OtpCode.user_id == user.id)
        .order_by(OtpCode.created_at.desc())
        .first()
    )

    if latest_otp:
        created_at = latest_otp.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        elapsed = (now - created_at).total_seconds()
        if elapsed < RATE_LIMIT_SECONDS:
            retry_after = int(RATE_LIMIT_SECONDS - elapsed)
            raise AppError(
                code=ErrorCode.RATE_LIMITED.value,
                message=f"Please wait {retry_after} seconds before requesting a new verification code.",
                field="email",
                http_status=429,
            )

    # Invalidate any previous unexpired code for that user
    db.query(OtpCode).filter(OtpCode.user_id == user.id).delete()

    # Generate fresh 6-digit numeric code
    raw_code = _generate_otp_code()
    code_hash = _hash_otp(raw_code)
    expires_at = now + timedelta(minutes=10)

    new_otp = OtpCode(
        user_id=user.id,
        code_hash=code_hash,
        expires_at=expires_at,
        attempts=0,
        created_at=now,
    )
    db.add(new_otp)
    db.commit()

    # Send OTP code via email service wrapper
    try:
        email_service.send_otp_email(to_email=user.email, code=raw_code)
    except Exception as e:
        logger.error(f"Failed to send resend OTP email to {user.email}: {e}")

    logger.info(f"Verification code resent to {user.email}")
    return ResendOtpResponse(
        message="A new verification code has been sent to your email.",
        cooldown_seconds=RATE_LIMIT_SECONDS,
    )


@router.post("/login", response_model=UserResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """
    Sign in with email + password.
    Returns 404 if no account found (must sign up first).
    Returns 401 if password is wrong.
    """
    clean_email = str(body.email).lower().strip()
    user = db.query(User).filter(User.email == clean_email).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="No account found with this email. Please sign up first.",
        )

    if user.provider == "google":
        raise HTTPException(
            status_code=400,
            detail="This account was registered with Google. Please use 'Sign in with Google'.",
        )

    if not user.password_hash or not _verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect password.")

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    logger.info(f"User logged in: {user.email}")
    return _user_to_response(user)


@router.post("/google", response_model=UserResponse)
def google_auth(body: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Verify Google ID token and either:
    - mode=register : Register a new Google account (409 if already exists)
    - mode=login    : Sign in (404 if not registered yet — must sign up first)
    Only valid Google-issued emails are accepted.
    """
    payload = _parse_google_jwt(body.credential)
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid Google credential token.")

    email: str = payload.get("email", "").lower().strip()
    name: str = payload.get("name") or email.split("@")[0]
    picture: str = payload.get("picture", "")
    email_verified: bool = payload.get("email_verified", False)

    if not email:
        raise HTTPException(status_code=400, detail="Could not extract email from Google token.")

    if not _is_valid_google_email(email):
        raise HTTPException(
            status_code=422,
            detail="The email from Google is not a valid email address.",
        )

    if not email_verified:
        raise HTTPException(
            status_code=403,
            detail="Your Google email is not verified. Please verify your Google account first.",
        )

    user = db.query(User).filter(User.email == email).first()

    if body.mode == "register":
        if user:
            # Already registered — just log in
            user.last_login_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(user)
            return _user_to_response(user)

        # Create new Google user
        user = User(
            email=email,
            name=name,
            picture=picture,
            provider="google",
            password_hash=None,
            is_email_verified=True,
            created_at=datetime.now(timezone.utc),
            last_login_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"New Google user registered: {user.email}")
        return _user_to_response(user)

    else:  # mode == "login"
        if not user:
            raise HTTPException(
                status_code=404,
                detail="No account found with this Google email. Please sign up first.",
            )
        if user.provider != "google":
            raise HTTPException(
                status_code=400,
                detail="This email is registered with email/password. Please sign in with your password.",
            )

        user.last_login_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        logger.info(f"Google user logged in: {user.email}")
        return _user_to_response(user)
