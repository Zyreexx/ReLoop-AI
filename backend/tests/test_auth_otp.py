"""
Tests for email format validation and OTP verification flow.
Covers:
- PART A: Email format validation via EmailStr, rejecting malformed emails with typed INVALID_INPUT and field='email'.
- PART B: OTP generation, SHA-256 hashing, delivery, verification, attempt limits, expiry, and rate-limited resend.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.models.entities import OtpCode, User
from app.errors import ErrorCode


@pytest.fixture
def db():
    """Provides the active test database session from FastAPI dependency overrides."""
    gen = app.dependency_overrides[get_db]()
    session = next(gen)
    try:
        yield session
    finally:
        try:
            next(gen)
        except StopIteration:
            pass


@pytest.fixture(autouse=True)
def mock_email_service(monkeypatch):
    """
    Ensure every test mocks email_service.send_email so no real external
    network calls or transactional emails are ever sent.
    """
    mock_send = MagicMock(return_value={"id": "mock_email_123", "status": "sent"})
    monkeypatch.setattr("app.services.email_service.send_email", mock_send)
    return mock_send


# ─────────────────────────────────────────────────────────────────────────────
# PART A — Email Format Validation Tests
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "malformed_email",
    [
        "not-an-email",
        "missing@domain",
        "@nodomain.com",
        "plainaddress",
        "user@",
        "user@.com",
    ],
)
def test_malformed_email_rejected_with_typed_error(client: TestClient, malformed_email: str):
    """
    Malformed emails must be automatically rejected at the request-validation layer
    via Pydantic's EmailStr type, returning typed format {"error": {"code", "message", "field"}}
    with field="email" and code="INVALID_INPUT".
    """
    # 1. Test /api/auth/register
    res = client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": malformed_email,
            "password": "validpassword123",
            "provider": "email",
        },
    )
    assert res.status_code == 422
    body = res.json()
    assert "error" in body
    assert body["error"]["code"] == ErrorCode.INVALID_INPUT.value
    assert body["error"]["field"] == "email"
    assert "email" in body["error"]["message"].lower()

    # 2. Test /api/auth/verify-otp
    res_verify = client.post(
        "/api/auth/verify-otp",
        json={"email": malformed_email, "code": "123456"},
    )
    assert res_verify.status_code == 422
    body_verify = res_verify.json()
    assert body_verify["error"]["code"] == ErrorCode.INVALID_INPUT.value
    assert body_verify["error"]["field"] == "email"

    # 3. Test /api/auth/resend-otp
    res_resend = client.post(
        "/api/auth/resend-otp",
        json={"email": malformed_email},
    )
    assert res_resend.status_code == 422
    body_resend = res_resend.json()
    assert body_resend["error"]["code"] == ErrorCode.INVALID_INPUT.value
    assert body_resend["error"]["field"] == "email"


# ─────────────────────────────────────────────────────────────────────────────
# PART B — OTP Verification & Flow Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_valid_email_signup_creates_user_and_otp(client: TestClient, db, mock_email_service):
    """
    Valid email registration creates user with is_email_verified=False,
    stores hashed OTP in separate OtpCode table (not plaintext), and invokes email_service.
    """
    res = client.post(
        "/api/auth/register",
        json={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "password123",
            "provider": "email",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "jane@example.com"
    assert data["name"] == "Jane Doe"
    assert data["is_email_verified"] is False

    # Check mock email call
    assert mock_email_service.called
    call_args = mock_email_service.call_args[1]
    assert call_args["to"] == "jane@example.com"
    assert "code" in call_args["text_content"].lower()

    # Check DB state
    user = db.query(User).filter(User.email == "jane@example.com").first()
    assert user is not None
    assert user.is_email_verified is False

    otp = db.query(OtpCode).filter(OtpCode.user_id == user.id).first()
    assert otp is not None
    assert otp.attempts == 0
    assert len(otp.code_hash) == 64  # SHA-256 hex digest length
    # Plaintext code must NOT be stored
    assert not hasattr(otp, "code") or otp.code_hash != "123456"


def test_verify_correct_otp_before_expiry(client: TestClient, db, mock_email_service):
    """
    Correct OTP submission marks user as is_email_verified=True, invalidates/deletes
    the OTP row, and subsequent submissions of the same code fail.
    """
    # 1. Register user
    res = client.post(
        "/api/auth/register",
        json={
            "name": "Bob Smith",
            "email": "bob@example.com",
            "password": "password123",
            "provider": "email",
        },
    )
    assert res.status_code == 201

    # Extract sent code from mock
    text_sent = mock_email_service.call_args[1]["text_content"]
    # text format: "Your ReLoop AI verification code is: 123456"
    code = [w for w in text_sent.replace("\n", " ").split() if w.isdigit() and len(w) == 6][0]

    # 2. Verify with correct OTP
    verify_res = client.post(
        "/api/auth/verify-otp",
        json={"email": "bob@example.com", "code": code},
    )
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["is_email_verified"] is True

    # 3. Check DB: user is verified and OTP row is deleted/invalidated
    db.expire_all()
    user = db.query(User).filter(User.email == "bob@example.com").first()
    assert user.is_email_verified is True
    otp = db.query(OtpCode).filter(OtpCode.user_id == user.id).first()
    assert otp is None  # Row invalidated/deleted

    # 4. Re-submitting the same code afterward fails
    re_verify = client.post(
        "/api/auth/verify-otp",
        json={"email": "bob@example.com", "code": code},
    )
    assert re_verify.status_code == 400
    err = re_verify.json()["error"]
    assert err["code"] == ErrorCode.INVALID_INPUT.value


def test_wrong_otp_increments_attempts_and_invalidates_at_limit(client: TestClient, db, mock_email_service):
    """
    Wrong OTP returns typed error and increments attempts.
    After fixed limit (5 attempts), the code is invalidated even if correct code
    is submitted afterward (requiring a fresh resend).
    """
    # 1. Register
    client.post(
        "/api/auth/register",
        json={
            "name": "Charlie",
            "email": "charlie@example.com",
            "password": "password123",
            "provider": "email",
        },
    )
    text_sent = mock_email_service.call_args[1]["text_content"]
    valid_code = [w for w in text_sent.replace("\n", " ").split() if w.isdigit() and len(w) == 6][0]
    wrong_code = "999999" if valid_code != "999999" else "888888"

    # 2. Attempts 1 to 4: increments attempts, returns OTP_INVALID
    for attempt in range(1, 5):
        res = client.post(
            "/api/auth/verify-otp",
            json={"email": "charlie@example.com", "code": wrong_code},
        )
        assert res.status_code == 400
        body = res.json()
        assert body["error"]["code"] == ErrorCode.OTP_INVALID.value
        assert body["error"]["field"] == "code"

        db.expire_all()
        user = db.query(User).filter(User.email == "charlie@example.com").first()
        otp = db.query(OtpCode).filter(OtpCode.user_id == user.id).first()
        assert otp.attempts == attempt

    # 3. Attempt 5: hits the limit, code is invalidated entirely
    res_5 = client.post(
        "/api/auth/verify-otp",
        json={"email": "charlie@example.com", "code": wrong_code},
    )
    assert res_5.status_code == 400
    body_5 = res_5.json()
    assert body_5["error"]["code"] == ErrorCode.OTP_ATTEMPTS_EXCEEDED.value
    assert body_5["error"]["field"] == "code"

    # Confirm OTP row was invalidated/deleted
    db.expire_all()
    user = db.query(User).filter(User.email == "charlie@example.com").first()
    otp = db.query(OtpCode).filter(OtpCode.user_id == user.id).first()
    assert otp is None

    # 4. Even submitting the correct code afterward must now fail
    res_correct_after_limit = client.post(
        "/api/auth/verify-otp",
        json={"email": "charlie@example.com", "code": valid_code},
    )
    assert res_correct_after_limit.status_code == 400
    assert res_correct_after_limit.json()["error"]["code"] == ErrorCode.INVALID_INPUT.value


def test_expired_otp_returns_distinct_typed_error(client: TestClient, db, mock_email_service):
    """
    Expired OTP returns typed error distinguishing "expired" (OTP_EXPIRED)
    from "wrong code" (OTP_INVALID).
    """
    client.post(
        "/api/auth/register",
        json={
            "name": "Dan",
            "email": "dan@example.com",
            "password": "password123",
            "provider": "email",
        },
    )
    text_sent = mock_email_service.call_args[1]["text_content"]
    valid_code = [w for w in text_sent.replace("\n", " ").split() if w.isdigit() and len(w) == 6][0]

    # Manually expire the OTP in DB
    user = db.query(User).filter(User.email == "dan@example.com").first()
    otp = db.query(OtpCode).filter(OtpCode.user_id == user.id).first()
    otp.expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    db.commit()

    # Submit valid code against expired record
    res = client.post(
        "/api/auth/verify-otp",
        json={"email": "dan@example.com", "code": valid_code},
    )
    assert res.status_code == 400
    body = res.json()
    assert body["error"]["code"] == ErrorCode.OTP_EXPIRED.value
    assert body["error"]["code"] != ErrorCode.OTP_INVALID.value
    assert body["error"]["field"] == "code"
    assert "expired" in body["error"]["message"].lower()


def test_resend_otp_invalidates_previous_and_enforces_rate_limit(client: TestClient, db, mock_email_service):
    """
    Resend OTP flow:
    - An immediate second resend call is rate-limited (429 RATE_LIMITED).
    - After cooldown, resend creates new OTP and invalidates previous one.
    - Previous code fails; newly issued code succeeds.
    """
    # 1. Initial registration
    client.post(
        "/api/auth/register",
        json={
            "name": "Eve",
            "email": "eve@example.com",
            "password": "password123",
            "provider": "email",
        },
    )
    code_1 = [w for w in mock_email_service.call_args[1]["text_content"].replace("\n", " ").split() if w.isdigit() and len(w) == 6][0]

    # 2. Immediate second request to /api/auth/resend-otp is rejected by rate limit
    res_immediate = client.post(
        "/api/auth/resend-otp",
        json={"email": "eve@example.com"},
    )
    assert res_immediate.status_code == 429
    body_imm = res_immediate.json()
    assert body_imm["error"]["code"] == ErrorCode.RATE_LIMITED.value
    assert body_imm["error"]["field"] == "email"

    # 3. Simulate passage of cooldown (> 60 seconds)
    db.expire_all()
    user = db.query(User).filter(User.email == "eve@example.com").first()
    otp = db.query(OtpCode).filter(OtpCode.user_id == user.id).first()
    otp.created_at = datetime.now(timezone.utc) - timedelta(seconds=65)
    db.commit()

    # 4. Now resend succeeds
    mock_email_service.reset_mock()
    res_resend = client.post(
        "/api/auth/resend-otp",
        json={"email": "eve@example.com"},
    )
    assert res_resend.status_code == 200
    assert "sent" in res_resend.json()["message"].lower()
    assert mock_email_service.called

    code_2 = [w for w in mock_email_service.call_args[1]["text_content"].replace("\n", " ").split() if w.isdigit() and len(w) == 6][0]

    # 5. Old code is invalidated and fails
    res_old = client.post(
        "/api/auth/verify-otp",
        json={"email": "eve@example.com", "code": code_1},
    )
    # If code_1 happens to equal code_2 (rare), this would pass, but they should be different
    if code_1 != code_2:
        assert res_old.status_code == 400

    # 6. New code succeeds
    res_new = client.post(
        "/api/auth/verify-otp",
        json={"email": "eve@example.com", "code": code_2},
    )
    assert res_new.status_code == 200
    assert res_new.json()["is_email_verified"] is True
