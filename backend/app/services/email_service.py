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

logger = logging.getLogger(__name__)

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
    """
    api_key = os.getenv("RESEND_API_KEY", RESEND_API_KEY).strip()
    from_address = os.getenv("EMAIL_FROM", EMAIL_FROM).strip()

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

    # Production / Live delivery via Resend HTTP API
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
