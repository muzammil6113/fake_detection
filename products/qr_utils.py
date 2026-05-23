import io
import qrcode
from django.core.files.base import ContentFile


def generate_qr(product_hash: str, verify_url: str) -> ContentFile:
    """Generate QR PNG encoding verify_url. Returns ContentFile for ImageField."""
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0a0e1a", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ContentFile(buf.read(), name=f"qr_{product_hash[:16]}.png")