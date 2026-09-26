import hashlib
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, UserAddress, PhoneAuthOTP, UserPhoneUpdateOTP, UserDevice


class RequestOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20, required=True)

    def validate_phone_number(self, value):
        cleaned = value.strip().replace(' ', '').replace('-', '')
        if len(cleaned) < 10:
            raise serializers.ValidationError("Please provide a valid phone number (at least 10 digits).")
        return cleaned


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20, required=True)
    otp_code = serializers.CharField(max_length=10, required=True)
    full_name = serializers.CharField(max_length=150, required=False, default="Devotee")

    def validate_phone_number(self, value):
        return value.strip().replace(' ', '').replace('-', '')


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'email', 'phone_number', 'phone_verified_at',
            'avatar_url', 'origin_state', 'origin_city', 'gotra', 'mother_tongue',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'phone_number', 'phone_verified_at', 'created_at']


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = [
            'id', 'address_type', 'custom_title', 'flat_house_building',
            'street_area_locality', 'city', 'state', 'postal_code',
            'landmark', 'latitude', 'longitude', 'is_default',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        user = self.context['request'].user
        # If user has no existing addresses, make this the default
        if not UserAddress.objects.filter(user=user).exists():
            validated_data['is_default'] = True
        return UserAddress.objects.create(user=user, **validated_data)


class UserDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevice
        fields = ['id', 'fcm_token', 'device_type', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class RequestPhoneUpdateSerializer(serializers.Serializer):
    new_phone_number = serializers.CharField(max_length=20, required=True)

    def validate_new_phone_number(self, value):
        cleaned = value.strip().replace(' ', '').replace('-', '')
        if User.objects.filter(phone_number=cleaned).exists():
            raise serializers.ValidationError("This phone number is already registered to another account.")
        return cleaned


class VerifyPhoneUpdateSerializer(serializers.Serializer):
    new_phone_number = serializers.CharField(max_length=20, required=True)
    otp_code = serializers.CharField(max_length=10, required=True)
