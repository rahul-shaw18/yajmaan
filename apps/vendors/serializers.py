from rest_framework import serializers
from .models import Vendor, VendorOnboardingApplication, VendorDevice, VendorLocationHistory
from apps.catalog.serializers import SubcategorySerializer


class CoordinateField(serializers.Field):
    """
    Safely parses and rounds geographical coordinates to 6 decimal places,
    preventing DecimalField max_digits overflow from high-precision JavaScript floats.
    """
    def to_internal_value(self, data):
        if data is None or data == '':
            return None
        try:
            val = float(data)
            return round(val, 6)
        except (ValueError, TypeError):
            raise serializers.ValidationError("Invalid coordinate value")

    def to_representation(self, value):
        return float(value) if value is not None else None


class VendorOnboardingApplicationSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="Pandit Ji")
    home_latitude = CoordinateField(required=False, allow_null=True)
    home_longitude = CoordinateField(required=False, allow_null=True)

    class Meta:
        model = VendorOnboardingApplication
        fields = [
            'id', 'full_name', 'phone_number', 'email', 'origin_state',
            'origin_city', 'qualification', 'experience_years', 'specializations',
            'address', 'home_latitude', 'home_longitude',
            'id_proof_type', 'id_proof_number', 'id_proof_document_url',
            'pan_card_number', 'pan_card_document_url',
            'bank_account_number', 'bank_ifsc_code', 'bank_beneficiary_name',
            'step_completed', 'status', 'rejection_reason', 'created_at', 'updated_at', 'reviewed_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'reviewed_at']


class VendorPublicProfileSerializer(serializers.ModelSerializer):
    onboarding_application = VendorOnboardingApplicationSerializer(read_only=True)
    home_latitude = CoordinateField(required=False, allow_null=True)
    home_longitude = CoordinateField(required=False, allow_null=True)
    current_latitude = CoordinateField(required=False, allow_null=True)
    current_longitude = CoordinateField(required=False, allow_null=True)
    id_proof_type = serializers.CharField(source='onboarding_application.id_proof_type', read_only=True, default='')
    id_proof_number = serializers.CharField(source='onboarding_application.id_proof_number', read_only=True, default='')
    id_proof_document_url = serializers.CharField(source='onboarding_application.id_proof_document_url', read_only=True, default='')
    pan_card_number = serializers.CharField(source='onboarding_application.pan_card_number', read_only=True, default='')
    pan_card_document_url = serializers.CharField(source='onboarding_application.pan_card_document_url', read_only=True, default='')
    bank_account_number = serializers.CharField(source='onboarding_application.bank_account_number', read_only=True, default='')
    bank_ifsc_code = serializers.CharField(source='onboarding_application.bank_ifsc_code', read_only=True, default='')
    bank_beneficiary_name = serializers.CharField(source='onboarding_application.bank_beneficiary_name', read_only=True, default='')

    class Meta:
        model = Vendor
        fields = [
            'id', 'name', 'phone_number', 'email', 'origin_state', 'origin_city',
            'qualification', 'experience_years', 'specializations', 'rating_average',
            'reviews_count', 'service_radius_km', 'is_active', 'is_available',
            'is_on_duty', 'address', 'home_latitude', 'home_longitude',
            'current_latitude', 'current_longitude', 'location_updated_at',
            'onboarding_application',
            'id_proof_type', 'id_proof_number', 'id_proof_document_url',
            'pan_card_number', 'pan_card_document_url',
            'bank_account_number', 'bank_ifsc_code', 'bank_beneficiary_name'
        ]


class VendorProfileUpdateSerializer(serializers.ModelSerializer):
    home_latitude = CoordinateField(required=False, allow_null=True)
    home_longitude = CoordinateField(required=False, allow_null=True)
    current_latitude = CoordinateField(required=False, allow_null=True)
    current_longitude = CoordinateField(required=False, allow_null=True)

    class Meta:
        model = Vendor
        fields = [
            'name', 'email', 'origin_state', 'origin_city',
            'qualification', 'experience_years', 'specializations',
            'address', 'home_latitude', 'home_longitude',
            'current_latitude', 'current_longitude', 'is_on_duty'
        ]


class VendorDeviceSerializer(serializers.ModelSerializer):
    vendor_id = serializers.UUIDField(required=True)

    class Meta:
        model = VendorDevice
        fields = ['id', 'vendor_id', 'fcm_token', 'device_type', 'updated_at']
        read_only_fields = ['id', 'updated_at']

    def create(self, validated_data):
        vendor_id = validated_data.pop('vendor_id')
        vendor = Vendor.objects.get(id=vendor_id)
        fcm_token = validated_data['fcm_token']
        device_type = validated_data.get('device_type', 'android')
        device, _ = VendorDevice.objects.update_or_create(
            vendor=vendor,
            fcm_token=fcm_token,
            defaults={'device_type': device_type}
        )
        return device


class VendorLocationUpdateSerializer(serializers.Serializer):
    vendor_id = serializers.UUIDField(required=True)
    latitude = serializers.DecimalField(
        max_digits=10,
        decimal_places=8,
        required=True,
        min_value=-90,
        max_value=90,
        help_text="Latitude (-90 to 90)"
    )
    longitude = serializers.DecimalField(
        max_digits=11,
        decimal_places=8,
        required=True,
        min_value=-180,
        max_value=180,
        help_text="Longitude (-180 to 180)"
    )


class VendorLocationResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    message = serializers.CharField()
    vendor_id = serializers.UUIDField()
    current_latitude = serializers.FloatField()
    current_longitude = serializers.FloatField()
    location_updated_at = serializers.DateTimeField()
    is_on_duty = serializers.BooleanField()


class VendorLocationHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorLocationHistory
        fields = ['id', 'vendor_id', 'latitude', 'longitude', 'created_at']
        read_only_fields = ['id', 'created_at']


class VendorDutyToggleSerializer(serializers.Serializer):
    vendor_id = serializers.UUIDField(required=True)
    is_on_duty = serializers.BooleanField(required=True)

