import hashlib
import jwt
import datetime
from django.conf import settings  # ✅ Add this

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(raw_password: str, hashed_password: str) -> bool:
    return hash_password(raw_password) == hashed_password

def generate_jwt(user_id):
    payload = {
        "user_id": str(user_id),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        "iat": datetime.datetime.utcnow(),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")  # ✅ Use settings.SECRET_KEY
    return token

def verify_jwt(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])  # ✅ Use settings.SECRET_KEY
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
