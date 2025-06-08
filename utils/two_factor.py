import pyotp
import qrcode
from io import BytesIO
import base64
from flask import current_app

def generate_secret():
    """Генерирует секретный ключ для 2FA."""
    return pyotp.random_base32()

def generate_totp(secret):
    """Создает объект TOTP для проверки кодов."""
    return pyotp.TOTP(secret)

def verify_totp(secret, token):
    """Проверяет введенный код."""
    totp = generate_totp(secret)
    return totp.verify(token)

def generate_qr_code(secret, username):
    """Генерирует QR-код для настройки 2FA."""
    totp = generate_totp(secret)
    provisioning_uri = totp.provisioning_uri(
        name=username,
        issuer_name=current_app.config['TWO_FACTOR_AUTH_ISSUER']
    )
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode() 