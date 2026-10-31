from django.utils import timezone
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import Vendor, VendorOnboardingApplication, VendorDevice, VendorLocationHistory
from .serializers import (
    VendorPublicProfileSerializer,
    VendorOnboardingApplicationSerializer,
    VendorDeviceSerializer,
    VendorLocationUpdateSerializer,
    VendorLocationResponseSerializer,
    VendorDutyToggleSerializer
)



class VendorOnboardingView(generics.CreateAPIView):
    queryset = VendorOnboardingApplication.objects.all()
    serializer_class = VendorOnboardingApplicationSerializer
    permission_classes = [AllowAny]


class VendorListView(generics.ListAPIView):
    queryset = Vendor.objects.filter(is_active=True, is_available=True)
    serializer_class = VendorPublicProfileSerializer
    permission_classes = [AllowAny]


class VendorDetailView(generics.RetrieveAPIView):
    queryset = Vendor.objects.filter(is_active=True)
    serializer_class = VendorPublicProfileSerializer
    lookup_field = 'id'
    permission_classes = [AllowAny]


class VendorDeviceView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=VendorDeviceSerializer,
        responses={200: VendorDeviceSerializer},
        description="Register or update vendor FCM push notification device token."
    )
    def post(self, request):
        serializer = VendorDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = serializer.save()
        return Response(VendorDeviceSerializer(device).data, status=status.HTTP_200_OK)


class VendorLocationView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=VendorLocationUpdateSerializer,
        responses={
            200: VendorLocationResponseSerializer,
            400: OpenApiResponse(description="Vendor is not on duty or invalid coordinates provided"),
            404: OpenApiResponse(description="Vendor not found")
        },
        description="Update vendor's live GPS coordinates (e.g. every 30 minutes from vendor device). Only allowed when vendor is on duty."
    )
    def post(self, request):
        return self._update_location(request)

    @extend_schema(
        request=VendorLocationUpdateSerializer,
        responses={
            200: VendorLocationResponseSerializer,
            400: OpenApiResponse(description="Vendor is not on duty or invalid coordinates provided"),
            404: OpenApiResponse(description="Vendor not found")
        },
        description="Update vendor's live GPS coordinates (e.g. every 30 minutes from vendor device). Only allowed when vendor is on duty."
    )
    def patch(self, request):
        return self._update_location(request)

    def _update_location(self, request):
        serializer = VendorLocationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vendor_id = serializer.validated_data['vendor_id']
        lat = serializer.validated_data['latitude']
        lon = serializer.validated_data['longitude']

        try:
            vendor = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            return Response(
                {"error": "NOT_FOUND", "detail": "Vendor not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # On-Duty Validation: Only allow location updates if vendor is currently on duty!
        if not vendor.is_on_duty:
            return Response(
                {
                    "error": "VENDOR_OFF_DUTY",
                    "detail": "Vendor is currently off duty. Location updates can only be saved when vendor is on duty.",
                    "is_on_duty": False,
                    "vendor_id": str(vendor.id)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        now = timezone.now()
        vendor.current_latitude = lat
        vendor.current_longitude = lon
        vendor.location_updated_at = now
        vendor.save(update_fields=['current_latitude', 'current_longitude', 'location_updated_at', 'updated_at'])

        # Record 30-minute periodic heartbeat in location history table
        VendorLocationHistory.objects.create(
            vendor=vendor,
            latitude=lat,
            longitude=lon
        )

        return Response({
            "status": "success",
            "message": "Vendor location recorded successfully.",
            "vendor_id": str(vendor.id),
            "current_latitude": float(vendor.current_latitude),
            "current_longitude": float(vendor.current_longitude),
            "location_updated_at": vendor.location_updated_at.isoformat(),
            "is_on_duty": vendor.is_on_duty
        }, status=status.HTTP_200_OK)


class VendorAvailableJobsView(APIView):
    """
    Returns jobs currently dispatched to this vendor that are still waiting to be accepted.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: OpenApiResponse(description="Returns active dispatched bookings for vendor")},
        description="List active dispatched booking requests for a specific vendor."
    )
    def get(self, request):
        vendor_id = request.query_params.get('vendor_id')
        if not vendor_id:
            return Response({"detail": "vendor_id query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            vendor = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            return Response({"detail": "Vendor not found."}, status=status.HTTP_404_NOT_FOUND)

        from apps.bookings.models import BookingDispatchLog, Booking
        from apps.bookings.serializers import BookingListSerializer

        # Find bookings dispatched to this vendor where response_status is DISPATCHED and booking is still SEARCHING_VENDOR or REQUESTED
        active_dispatches = BookingDispatchLog.objects.filter(
            vendor=vendor,
            response_status='DISPATCHED',
            booking__status__in=[Booking.BookingStatus.REQUESTED, Booking.BookingStatus.SEARCHING_VENDOR]
        ).select_related('booking', 'booking__service', 'booking__user', 'booking__address')

        bookings = [log.booking for log in active_dispatches]
        serializer = BookingListSerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class VendorDutyView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=VendorDutyToggleSerializer,
        responses={200: VendorPublicProfileSerializer},
        description="Toggle vendor onDuty status ON or OFF."
    )
    def patch(self, request):
        serializer = VendorDutyToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vendor_id = serializer.validated_data['vendor_id']
        is_on_duty = serializer.validated_data['is_on_duty']

        try:
            vendor = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            return Response({"detail": "Vendor not found."}, status=status.HTTP_404_NOT_FOUND)

        vendor.is_on_duty = is_on_duty
        vendor.save(update_fields=['is_on_duty', 'updated_at'])

        return Response(VendorPublicProfileSerializer(vendor).data, status=status.HTTP_200_OK)

