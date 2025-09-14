import hashlib
import jwt
import datetime
import random
import requests
from django.conf import settings
from django.core.mail import send_mail

# ---------------- PASSWORD HASHING ---------------- #
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(raw_password: str, hashed_password: str) -> bool:
    return hash_password(raw_password) == hashed_password

# ---------------- JWT ---------------- #
def generate_jwt(user_id):
    payload = {
        "user_id": str(user_id),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        "iat": datetime.datetime.utcnow(),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token

def verify_jwt(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# ---------------- OTP GENERATION ---------------- #
def generate_otp():
    """Generate a 6-digit random OTP."""
    return random.randint(100000, 999999)

# ---------------- SEND PHONE OTP (FAST2SMS) ---------------- #

def send_otp_to_phone(phone, otp):
    """
    Send OTP to phone using Fast2SMS
    """
    try:
        url = "https://www.fast2sms.com/dev/bulkV2"
        payload = {"variables_values": otp, "route": "otp", "numbers": phone}
        headers = {
            "authorization": settings.FAST2SMS_API_KEY,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        response = requests.post(url, data=payload, headers=headers)
        return response.json()  # optional, to check status
    except Exception as e:
        print(f"⚠️ SMS send failed: {e}")
        return None

# ---------------- SEND EMAIL OTP ---------------- #
def send_otp_to_email(email, otp):
    """Send OTP to email using Django's send_mail."""
    try:
        send_mail(
            subject="Verify Your Account",
            message=f"Your verification code is: {otp}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,  # ✅ Debugging ke liye false rakho
        )
        return True
    except Exception as e:
        print("❌ Error sending Email:", str(e))
        return False
