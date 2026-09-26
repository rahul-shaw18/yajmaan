from rest_framework import serializers
from apps.catalog.models import Service
from apps.accounts.models import UserAddress
from apps.vendors.models import Vendor
from apps.vendors.serializers import VendorPublicProfileSerializer
from apps.catalog.serializers import PoojaSamagriItemSerializer
from .models import Booking, Payment, BookingDispatchLog
from .dispatch import dispatch_booking_to_vendors


class CreateBookingSerializer(serializers.Serializer):
    service_id = serializers.UUIDField(required=True)
    address_id = serializers.UUIDField(required=True)
    pricing_variant = serializers.ChoiceField(choices=Booking.PricingVariant.choices, default=Booking.PricingVariant.WITH_SAMAGRI)
    preferred_date = serializers.DateField(required=True)
    preferred_time_slot = serializers.CharField(max_length=64, required=True)
    payment_mode = serializers.ChoiceField(choices=Payment.PaymentMode.choices, default=Payment.PaymentMode.PAY_NOW)

    def validate(self, attrs):
        user = self.context['request'].user
        
        # Validate service
        try:
            service = Service.objects.get(id=attrs['service_id'], is_active=True)
        except Service.DoesNotExist:
            raise serializers.ValidationError({"service_id": "Selected service is invalid or inactive."})

        # Validate address
        try:
            address = UserAddress.objects.get(id=attrs['address_id'], user=user)
        except UserAddress.DoesNotExist:
            raise serializers.ValidationError({"address_id": "Address not found for current user."})

        # Check coordinates (fallback to default city coordinates if null)
        if address.latitude is None or address.longitude is None:
            address.latitude = 28.6139  # New Delhi default
            address.longitude = 77.2090
            address.save(update_fields=['latitude', 'longitude'])

        attrs['service_obj'] = service
        attrs['address_obj'] = address
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        service = validated_data['service_obj']
        address = validated_data['address_obj']
        pricing_variant = validated_data['pricing_variant']
        payment_mode = validated_data.get('payment_mode', Payment.PaymentMode.PAY_NOW)

        # Price calculation
        if pricing_variant == Booking.PricingVariant.WITH_SAMAGRI:
            total_price = service.price_with_samagri
        else:
            total_price = service.price_without_samagri

        # Address snapshot
        snapshot_address = {
            "flat_house_building": address.flat_house_building,
            "street_area_locality": address.street_area_locality,
            "city": address.city,
            "state": address.state,
            "postal_code": address.postal_code,
            "landmark": address.landmark,
            "latitude": str(address.latitude),
            "longitude": str(address.longitude),
            "address_type": address.address_type,
        }

        # Spiritual origin snapshot (for Pooja vertical and priority matching)
        snapshot_origin = {
            "origin_state": user.origin_state or "",
            "origin_city": user.origin_city or "",
            "gotra": user.gotra or "",
            "mother_tongue": user.mother_tongue or "",
        }

        # Create Booking
        booking = Booking.objects.create(
            user=user,
            service=service,
            address=address,
            pricing_variant=pricing_variant,
            total_price=total_price,
            preferred_date=validated_data['preferred_date'],
            preferred_time_slot=validated_data['preferred_time_slot'],
            snapshot_booking_address=snapshot_address,
            snapshot_user_spiritual_origin=snapshot_origin,
            status=Booking.BookingStatus.REQUESTED
        )

        # Record payment
        Payment.objects.create(
            booking=booking,
            amount=total_price,
            payment_mode=payment_mode,
            status=Payment.PaymentStatus.COMPLETED if payment_mode == Payment.PaymentMode.PAY_NOW else Payment.PaymentStatus.PENDING,
            transaction_id=f"TXN-{str(booking.id)[:8].upper()}" if payment_mode == Payment.PaymentMode.PAY_NOW else None
        )

        # Trigger Assignment Engine & FCM Push Dispatch
        dispatch_booking_to_vendors(booking)

        return booking


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'amount', 'payment_mode', 'status', 'transaction_id', 'created_at']


from drf_spectacular.utils import extend_schema_field

class BookingListSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_banner = serializers.CharField(source='service.banner_image_url', read_only=True)
    category_name = serializers.CharField(source='service.category.name', read_only=True)
    vendor_name = serializers.CharField(source='vendor.name', default="Assigning shortly...", read_only=True)
    payment_mode = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'service_name', 'service_banner', 'category_name',
            'preferred_date', 'preferred_time_slot', 'pricing_variant',
            'total_price', 'status', 'vendor_name', 'payment_mode',
            'created_at'
        ]

    @extend_schema_field(serializers.CharField())
    def get_payment_mode(self, obj):
        latest_payment = obj.payments.first()
        return latest_payment.payment_mode if latest_payment else "PAY_NOW"


class BookingDetailSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_banner = serializers.CharField(source='service.banner_image_url', read_only=True)
    service_about = serializers.CharField(source='service.about', read_only=True)
    samagri_items = PoojaSamagriItemSerializer(source='service.samagri_items', many=True, read_only=True)
    assigned_vendor = VendorPublicProfileSerializer(source='vendor', read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'service_name', 'service_banner', 'service_about',
            'preferred_date', 'preferred_time_slot', 'pricing_variant',
            'total_price', 'status', 'assigned_vendor', 'snapshot_booking_address',
            'snapshot_user_spiritual_origin', 'samagri_items', 'payments',
            'created_at', 'updated_at'
        ]


class VendorActionSerializer(serializers.Serializer):
    vendor_id = serializers.UUIDField(required=True)
