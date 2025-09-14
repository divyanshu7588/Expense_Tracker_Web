# accounts/serializers.py
from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):  # ✅ ModelSerializer, na ki ModelSerializers
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active']
