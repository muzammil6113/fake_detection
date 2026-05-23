"""
SendGrid email + Twilio SMS.
Falls back to console print when API keys not set (dev mode).
Never crashes — alerts are best-effort.
"""
from django.conf import settings


def send_email(to: str, subject: str, body: str):
    if not settings.SENDGRID_API_KEY:
        print(f"\n[EMAIL→{to}] {subject}\n{body}\n")
        return
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail
        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        sg.client.mail.send.post(request_body=Mail(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_emails=to, subject=subject,
            plain_text_content=body,
        ).get())
    except Exception as e:
        print(f"[SendGrid error] {e}")


def send_sms(to: str, body: str):
    if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN,
                settings.TWILIO_PHONE_NUMBER, to]):
        print(f"\n[SMS→{to}] {body}\n")
        return
    try:
        from twilio.rest import Client
        Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN).messages.create(
            body=body, from_=settings.TWILIO_PHONE_NUMBER, to=to
        )
    except Exception as e:
        print(f"[Twilio error] {e}")


def alert_suspicious_scan(unit, scan, manufacturer):
    subject = f"⚠️ BlockVerify — Suspicious scan on {unit.serial_number}"
    body = (
        f"Hello {manufacturer.get_full_name() or manufacturer.username},\n\n"
        f"Suspicious activity detected on your product:\n\n"
        f"  Serial   : {unit.serial_number}\n"
        f"  Product  : {unit.model.name}\n"
        f"  Result   : {scan.result}\n"
        f"  Scan IP  : {scan.scanner_ip}\n"
        f"  Location : {scan.geo_city}, {scan.geo_country}\n\n"
        f"Log in to BlockVerify to review the full scan history.\n\n"
        f"— BlockVerify Security System"
    )
    if manufacturer.email:
        send_email(manufacturer.email, subject, body)
    if manufacturer.phone:
        send_sms(manufacturer.phone,
                 f"BlockVerify ALERT: Suspicious scan on {unit.serial_number} "
                 f"from {scan.geo_city or scan.scanner_ip}. Result: {scan.result}.")