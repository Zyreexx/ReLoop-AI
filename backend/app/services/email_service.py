"""
Transactional email service for ReLoop AI.
Uses Resend as the transactional email provider.
If RESEND_API_KEY is not configured, automatically operates in sandbox/test mode
so local development and offline environments function seamlessly.
"""
import logging
import os
from typing import Optional
import httpx

from pathlib import Path
from dotenv import load_dotenv

backend_env = Path(__file__).resolve().parent.parent / ".env"
root_env = Path(__file__).resolve().parent.parent.parent / ".env"
if backend_env.exists():
    load_dotenv(backend_env, override=True)
if root_env.exists():
    load_dotenv(root_env, override=True)
load_dotenv()

from app.config import settings

logger = logging.getLogger(__name__)

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

RESEND_API_URL = "https://api.resend.com/emails"
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "onboarding@resend.dev")


def send_email(
    to: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
) -> dict:
    """
    Thin isolated email delivery function.
    Mock this function in tests to prevent any external network calls.
    Supports:
    1. Direct SMTP (e.g. Gmail App Password) if SMTP_HOST and SMTP_USER are set.
    2. Resend HTTP API if RESEND_API_KEY is configured.
    3. Sandbox mode fallback if neither is configured.
    """
    api_key = (os.getenv("RESEND_API_KEY") or getattr(settings, "RESEND_API_KEY", "") or RESEND_API_KEY).strip()
    from_address = (os.getenv("EMAIL_FROM") or getattr(settings, "EMAIL_FROM", "onboarding@resend.dev") or EMAIL_FROM).strip()

    smtp_host = (os.getenv("SMTP_HOST") or getattr(settings, "SMTP_HOST", "")).strip()
    smtp_user = (os.getenv("SMTP_USER") or getattr(settings, "SMTP_USER", "")).strip()
    smtp_pass = (os.getenv("SMTP_PASS") or getattr(settings, "SMTP_PASS", "")).strip()
    smtp_port = int(os.getenv("SMTP_PORT") or getattr(settings, "SMTP_PORT", 587))

    # Priority 1: SMTP (e.g. Gmail) — sends to ANY email without custom domain verification
    if smtp_host and smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_address or smtp_user
            msg["To"] = to
            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(smtp_host, smtp_port, timeout=12.0) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(from_address or smtp_user, [to], msg.as_string())
            logger.info(f"Email sent successfully to {to} via SMTP ({smtp_host})")
            return {"id": "smtp_email_id", "status": "sent", "to": to}
        except Exception as e:
            logger.error(f"Failed to send email via SMTP to {to}: {e}", exc_info=True)
            raise

    # Sandbox / Test Mode fallback when no API key is configured
    if not api_key:
        logger.info(
            f"[EMAIL SANDBOX MODE] Email to '{to}' with subject '{subject}'. "
            f"No RESEND_API_KEY configured. (Content preview: {text_content or html_content[:60]}...)"
        )
        return {
            "id": "sandbox_email_id",
            "status": "sandbox",
            "to": to,
            "subject": subject,
        }

    # Priority 2: Resend HTTP API
    payload = {
        "from": from_address,
        "to": [to],
        "subject": subject,
        "html": html_content,
    }
    if text_content:
        payload["text"] = text_content

    try:
        response = httpx.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10.0,
        )
        response.raise_for_status()
        result = response.json()
        logger.info(f"Email sent successfully to {to} via Resend (id={result.get('id')})")
        return result
    except httpx.HTTPStatusError as e:
        error_msg = ""
        try:
            err_json = e.response.json()
            error_msg = err_json.get("message", "")
        except Exception:
            error_msg = e.response.text
        logger.error(f"Failed to send email via Resend to {to} ({e.response.status_code}): {error_msg}")
        if e.response.status_code == 403 and "only send testing emails" in error_msg:
            print(
                f"\n" + "=" * 65 + "\n"
                f" [RESEND NOTICE: EMAIL NOT DELIVERED]\n"
                f" Resend free tier only sends test emails to: rushilparmar991@gmail.com\n"
                f" Recipient requested: {to}\n\n"
                f" SOLUTIONS TO RECEIVE REAL EMAILS:\n"
                f" 1. Add free Gmail App Password to backend/.env (SMTP_USER, SMTP_PASS)\n"
                f"    -> Delivers immediately to ANY email address in the world!\n"
                f" 2. Or test by signing up with: rushilparmar991@gmail.com\n"
                f" 3. Or verify your domain at resend.com/domains\n"
                f" For now, use the verification code shown above in this terminal.\n"
                f"=" * 65 + "\n",
                flush=True,
            )
        raise
    except Exception as e:
        logger.error(f"Failed to send email via Resend to {to}: {e}", exc_info=True)
        raise


def send_otp_email(to_email: str, code: str) -> dict:
    """
    Send a 6-digit OTP verification code to a user's email address.
    """
    subject = "Verify your email for ReLoop AI"
    text_content = (
        f"Your ReLoop AI verification code is: {code}\n\n"
        f"This code will expire in 10 minutes. "
        f"If you did not request this code, please ignore this email."
    )
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Verify your email for ReLoop AI</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f5f5f7; margin: 0; padding: 20px; }}
            .container {{ max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 16px; padding: 40px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); }}
            .brand {{ font-size: 22px; font-weight: 700; color: #1d1d1f; margin-bottom: 24px; }}
            .brand span {{ color: #0071E3; }}
            h1 {{ font-size: 20px; color: #1d1d1f; margin-bottom: 12px; }}
            p {{ font-size: 15px; color: #6e6e73; line-height: 1.5; margin-bottom: 20px; }}
            .code-box {{ background: #f5f5f7; border-radius: 12px; padding: 20px; text-align: center; margin: 28px 0; }}
            .code {{ font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #0071E3; font-family: monospace; }}
            .footer {{ font-size: 12px; color: #86868b; border-top: 1px solid #e5e5ea; padding-top: 20px; margin-top: 32px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="brand">ReLoop<span>AI</span></div>
            <h1>Email Verification Code</h1>
            <p>Thank you for signing up for ReLoop AI. Use the 6-digit verification code below to verify your email address:</p>
            <div class="code-box">
                <div class="code">{code}</div>
            </div>
            <p>This verification code is valid for <strong>10 minutes</strong>. If you did not create a ReLoop AI account, no further action is required.</p>
            <div class="footer">
                &copy; ReLoop AI — Hardware Life-Extension & Circular Decision Platform
            </div>
        </div>
    </body>
    </html>
    """
    return send_email(
        to=to_email,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
    )
