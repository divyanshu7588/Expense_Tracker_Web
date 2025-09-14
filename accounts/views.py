from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import check_password
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import requests
import datetime

from .models import User
from .serializers import UserSerializer
from .utils import generate_jwt, verify_jwt, generate_otp  # ✅ send_otp_to_phone hata diya

# ---------------- REGISTER VIEW ---------------- #
class RegisterView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        phone = request.data.get('phone')

        if not email or not password or not phone:
            return Response({"error": "Email, phone and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already registered"}, status=status.HTTP_400_BAD_REQUEST)

        user = User(email=email, first_name=first_name, last_name=last_name, phone=phone, is_active=False)
        user.set_password(password)

        otp = generate_otp()
        user.otp = otp
        user.otp_expiry = timezone.now() + datetime.timedelta(minutes=5)
        user.save()

        try:
            # ✅ Send Email OTP
            send_mail(
                subject="Verify your account",
                message=f"Your OTP is {otp}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            return Response({"error": f"Email send failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            # ✅ Send Phone OTP
            url = "https://www.fast2sms.com/dev/bulkV2"
            payload = {"variables_values": otp, "route": "otp", "numbers": phone}
            headers = {
                "authorization": settings.FAST2SMS_API_KEY,
                "Content-Type": "application/x-www-form-urlencoded",
            }
            resp = requests.post(url, data=payload, headers=headers)
            print("SMS API Response:", resp.status_code, resp.text)
        except Exception as e:
            print(f"⚠️ SMS send failed: {str(e)}")

        return Response({"message": "User created, OTP sent to email and phone"}, status=status.HTTP_201_CREATED)
# ---------------- VERIFY OTP VIEW ---------------- #
class VerifyOTPView(APIView):
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        if not email or not otp:
            return Response({"error": "Email and OTP are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # ✅ Check OTP exists
        if not user.otp or not user.otp_expiry:
            return Response({"error": "No OTP generated. Please request again."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Check OTP expiry
        if timezone.now() > user.otp_expiry:
            # Expired -> clear OTP
            user.otp = None
            user.otp_expiry = None
            user.save()
            return Response({"error": "OTP expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Check OTP match
        if str(user.otp) != str(otp):
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Success: Activate user and clear OTP
        user.is_active = True
        user.otp = None
        user.otp_expiry = None
        user.save()

        # ✅ Generate JWT Token
        token = generate_jwt(user.id)

        serializer = UserSerializer(user)
        return Response(
            {
                "message": "OTP verified successfully! Your account is now active.",
                "token": token,
                "user": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
# ---------------- LOGIN VIEW ---------------- #
class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({"error": "Account not verified. Please verify OTP first."}, status=status.HTTP_403_FORBIDDEN)

        if not check_password(password, user.password):
            return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

        token = generate_jwt(user.id)
        serializer = UserSerializer(user)
        return Response({"token": token, "user": serializer.data}, status=status.HTTP_200_OK)

from rest_framework.permissions import IsAuthenticated

class GetUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
