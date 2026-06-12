"""
Alert utilities for BlockVerify.
Sends suspicious-scan alerts to manufacturers via Gmail SMTP.
Falls back to console print in dev mode (when EMAIL_HOST_USER is not set).
Never crashes — alerts are best-effort.
"""
import logging
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str):
    """
    Send an email using Django's configured email backend (Gmail SMTP).
    Falls back to console print if EMAIL_HOST_USER is not configured.
    """
    if not getattr(settings, 'EMAIL_HOST_USER', ''):
        # Dev fallback — print to console
        print(f"\n[EMAIL → {to}]\nSubject: {subject}\n{body}\n")
        return

    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to],
            fail_silently=False,
        )
        logger.info(f"Alert email sent to {to}")
    except Exception as e:
        # Log but don't crash the scan flow
        logger.error(f"Failed to send alert email to {to}: {e}")
        print(f"[Email error] {e}")


def send_sms(to: str, body: str):
    """
    Send SMS via Twilio. Optional — skips silently if keys not set.
    """
    if not all([
        getattr(settings, 'TWILIO_ACCOUNT_SID', ''),
        getattr(settings, 'TWILIO_AUTH_TOKEN', ''),
        getattr(settings, 'TWILIO_PHONE_NUMBER', ''),
        to,
    ]):
        print(f"\n[SMS → {to}] {body}\n")
        return

    try:
        from twilio.rest import Client
        Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN).messages.create(
            body=body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to,
        )
        logger.info(f"Alert SMS sent to {to}")
    except Exception as e:
        logger.error(f"Failed to send SMS to {to}: {e}")
        print(f"[Twilio error] {e}")


def alert_suspicious_scan(unit, scan, manufacturer):
    """
    Send a suspicious scan alert to the manufacturer.

    Args:
        unit         – ProductUnit instance
        scan         – ScanLog (products.models.ScanLog) instance
        manufacturer – User instance with role=MANUFACTURER
    """
    name = manufacturer.get_full_name() or manufacturer.username
    company = f" ({manufacturer.company_name})" if manufacturer.company_name else ""

    subject = f"⚠️ BlockVerify Alert — Suspicious scan on {unit.serial_number}"

    body = (
        f"Hello {name}{company},\n\n"
        f"Suspicious activity was detected on one of your registered products.\n\n"
        f"─────────────────────────────────\n"
        f"  Product  : {unit.model.name if unit.model else 'Unknown'}\n"
        f"  Serial   : {unit.serial_number}\n"
        f"  Result   : {scan.result}\n"
        f"  Scanned  : {scan.scanned_at.strftime('%Y-%m-%d %H:%M:%S')} IST\n"
        f"  Scanner IP: {scan.scanner_ip or 'Unknown'}\n"
        f"  Location : {scan.geo_city or '—'}, {scan.geo_country or '—'}\n"
        f"─────────────────────────────────\n\n"
        f"This may indicate a counterfeit product or a cloning attack.\n"
        f"Log in to BlockVerify to review the full scan history.\n\n"
        f"— BlockVerify Security System"
    )

    if manufacturer.email:
        send_email(manufacturer.email, subject, body)
    else:
        logger.warning(
            f"Manufacturer {manufacturer.username} has no email — alert skipped."
        )

    # Optional SMS (only if manufacturer.phone is filled)
    if getattr(manufacturer, 'phone', None):
        sms_body = (
            f"BlockVerify ALERT: Suspicious scan on {unit.serial_number} "
            f"from {scan.geo_city or scan.scanner_ip or 'unknown location'}. "
            f"Check your dashboard."
        )
        send_sms(manufacturer.phone, sms_body)