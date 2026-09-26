from rest_framework import serializers
from .models import Vendor, VendorOnboardingApplication, VendorDevice
from apps.catalog.serializers import SubcategorySerializer


class VendorPublicProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = [
            'id', 'name', 'phone_number', 'origin_state', 'origin_city',
            'qualification', 'experience_years', 'rating_average',
            'reviews_count', 'service_radius_km'
        ]


class VendorOnboardingApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorOnboardingApplication
        fields = [
            'id', 'full_name', 'phone_number', 'email', 'origin_state',
            'origin_city', 'qualification', 'id_proof_type', 'id_proof_number',
            'id_proof_document_url', 'pan_card_number', 'pan_card_document_url',
            'bank_account_number', 'bank_ifsc_code', 'bank_beneficiary_name',
            'status', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'created_at']


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
    latitude = serializers.DecimalField(max_digits=10, decimal_places=8, required=True)
    longitude = serializers.DecimalField(max_digits=11, decimal_places=8, required=True)
