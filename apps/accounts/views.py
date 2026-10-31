import hashlib
import random
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import User, UserAddress, PhoneAuthOTP, UserPhoneUpdateOTP, UserDevice
from .serializers import (
    RequestOTPSerializer,
    VerifyOTPSerializer,
    UserProfileSerializer,
    UserAddressSerializer,
    UserDeviceSerializer,
    RequestPhoneUpdateSerializer,
    VerifyPhoneUpdateSerializer
)


from apps.core.sms import send_fast2sms_otp


def hash_otp(phone: str, otp: str) -> str:
    salt = settings.SECRET_KEY[:10]
    return hashlib.sha256(f"{salt}:{phone}:{otp}".encode()).hexdigest()


class RequestOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=RequestOTPSerializer,
        responses={
            200: OpenApiResponse(description="OTP sent successfully via SMS"),
            502: OpenApiResponse(description="SMS gateway delivery failure"),
        },
        description="Request an OTP via Fast2SMS for phone number authentication (Login or Signup)."
    )
    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone_number']

        # Determine OTP (use configured dev mock if explicitly set, otherwise generate secure 6-digit random code)
        dev_mock = getattr(settings, 'DEV_MOCK_OTP', None)
        if dev_mock:
            otp = str(dev_mock)
        else:
            otp = f"{random.randint(100000, 999999)}"

        expires_at = timezone.now() + timedelta(minutes=10)
        otp_hash = hash_otp(phone, otp)

        PhoneAuthOTP.objects.create(
            phone_number=phone,
            otp_hash=otp_hash,
            expires_at=expires_at
        )

        # Dispatch real SMS via Fast2SMS API
        sms_result = send_fast2sms_otp(phone_number=phone, otp_code=otp)

        if not sms_result["success"]:
            return Response({
                "detail": f"Failed to send SMS OTP: {sms_result.get('message', 'SMS gateway error')}",
                "phone_number": phone
            }, status=status.HTTP_502_BAD_GATEWAY)

        # Log OTP directly to server terminal
        print(f"\n==========================================")
        print(f"[AUTH OTP] Phone: {phone} | OTP: {otp}")
        print(f"==========================================\n")

        response_data = {
            "message": "OTP has been sent to your phone number.",
            "phone_number": phone,
            "expires_in_seconds": 600,
        }

        return Response(response_data, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=VerifyOTPSerializer,
        responses={200: OpenApiResponse(description="Returns user profile and JWT auth tokens")},
        description="Verify OTP to authenticate user and obtain JWT tokens."
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone_number']
        otp = serializer.validated_data['otp_code']
        full_name = serializer.validated_data.get('full_name', 'Devotee')

        now = timezone.now()
        expected_hash = hash_otp(phone, otp)
        dev_mock = getattr(settings, 'DEV_MOCK_OTP', None)
        is_dev_otp = bool(dev_mock and otp == dev_mock)

        # Check for valid unexpired OTP
        recent_otp = PhoneAuthOTP.objects.filter(
            phone_number=phone,
            expires_at__gte=now,
            is_verified=False
        ).order_by('-created_at').first()

        if not recent_otp and not is_dev_otp:
            return Response(
                {"detail": "Invalid or expired OTP. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not is_dev_otp and recent_otp.otp_hash != expected_hash:
            recent_otp.attempts_count += 1
            recent_otp.save(update_fields=['attempts_count'])
            return Response(
                {"detail": "Incorrect OTP. Please check and try again."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if recent_otp:
            recent_otp.is_verified = True
            recent_otp.save(update_fields=['is_verified'])

        # Get or create user
        user, created = User.objects.get_or_create(
            phone_number=phone,
            defaults={
                'full_name': full_name,
                'phone_verified_at': now,
            }
        )
        if not user.phone_verified_at:
            user.phone_verified_at = now
            user.save(update_fields=['phone_verified_at'])

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Authentication successful",
            "is_new_user": created,
            "user": UserProfileSerializer(user).data,
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        }, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserProfileSerializer},
        description="Retrieve profile details of the authenticated user."
    )
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer},
        description="Update profile details (name, email, origin state/city, gotra, mother tongue)."
    )
    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserAddressViewSet(viewsets.ModelViewSet):
    queryset = UserAddress.objects.none()
    serializer_class = UserAddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return UserAddress.objects.none()
        return UserAddress.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='set-default')
    def set_default(self, request, pk=None):
        address = self.get_object()
        address.is_default = True
        address.save()
        return Response(UserAddressSerializer(address).data, status=status.HTTP_200_OK)


class UserDeviceView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=UserDeviceSerializer,
        responses={200: UserDeviceSerializer},
        description="Register or update customer FCM device push notification token."
    )
    def post(self, request):
        serializer = UserDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fcm_token = serializer.validated_data['fcm_token']
        device_type = serializer.validated_data.get('device_type', 'android')

        device, _ = UserDevice.objects.update_or_create(
            user=request.user,
            fcm_token=fcm_token,
            defaults={'device_type': device_type}
        )
        return Response(UserDeviceSerializer(device).data, status=status.HTTP_200_OK)


class RequestPhoneUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=RequestPhoneUpdateSerializer,
        responses={200: OpenApiResponse(description="OTP sent for phone number update")},
        description="Request an OTP to update authenticated user's phone number."
    )
    def post(self, request):
        serializer = RequestPhoneUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_phone = serializer.validated_data['new_phone_number']

        dev_mock = getattr(settings, 'DEV_MOCK_OTP', None)
        otp = str(dev_mock) if dev_mock else f"{random.randint(100000, 999999)}"
        otp_hash = hash_otp(new_phone, otp)
        expires_at = timezone.now() + timedelta(minutes=10)

        UserPhoneUpdateOTP.objects.create(
            user=request.user,
            new_phone_number=new_phone,
            otp_hash=otp_hash,
            expires_at=expires_at
        )

        sms_result = send_fast2sms_otp(phone_number=new_phone, otp_code=otp)
        if not sms_result["success"]:
            return Response({
                "detail": f"Failed to send SMS OTP: {sms_result.get('message', 'SMS gateway error')}",
                "new_phone_number": new_phone
            }, status=status.HTTP_502_BAD_GATEWAY)

        res = {"message": f"OTP sent to {new_phone} for phone number update."}
        if sms_result.get("simulated"):
            res["note"] = "Simulated in development mode. Set FAST2SMS_API_KEY in .env to receive actual SMS."
            res["dev_otp"] = otp
        elif settings.DEBUG and dev_mock:
            res["dev_otp"] = otp
        return Response(res, status=status.HTTP_200_OK)


class VerifyPhoneUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=VerifyPhoneUpdateSerializer,
        responses={200: OpenApiResponse(description="Phone number updated successfully")},
        description="Verify OTP and update user's phone number."
    )
    def post(self, request):
        serializer = VerifyPhoneUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_phone = serializer.validated_data['new_phone_number']
        otp = serializer.validated_data['otp_code']

        now = timezone.now()
        expected_hash = hash_otp(new_phone, otp)
        is_dev_otp = settings.DEBUG and (otp == getattr(settings, 'DEV_MOCK_OTP', '123456'))

        record = UserPhoneUpdateOTP.objects.filter(
            user=request.user,
            new_phone_number=new_phone,
            expires_at__gte=now,
            is_verified=False
        ).order_by('-created_at').first()

        if not record and not is_dev_otp:
            return Response({"detail": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)

        if not is_dev_otp and record.otp_hash != expected_hash:
            return Response({"detail": "Incorrect OTP."}, status=status.HTTP_400_BAD_REQUEST)

        if record:
            record.is_verified = True
            record.save(update_fields=['is_verified'])

        request.user.phone_number = new_phone
        request.user.phone_verified_at = now
        request.user.save(update_fields=['phone_number', 'phone_verified_at'])

        return Response({"message": "Phone number successfully updated", "phone_number": new_phone})
