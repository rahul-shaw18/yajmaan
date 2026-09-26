from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import Booking
from .serializers import (
    CreateBookingSerializer,
    BookingListSerializer,
    BookingDetailSerializer,
    VendorActionSerializer
)
from .dispatch import (
    accept_booking,
    reject_booking,
    dispatch_booking_to_vendors,
    BookingAlreadyAcceptedError,
    BookingInvalidStateError
)
from apps.vendors.models import Vendor


class BookingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).select_related('service', 'vendor', 'address')

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateBookingSerializer
        elif self.action == 'retrieve':
            return BookingDetailSerializer
        return BookingListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        return Response(
            BookingDetailSerializer(booking).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        booking = self.get_object()
        if booking.status in [Booking.BookingStatus.COMPLETED, Booking.BookingStatus.CANCELLED]:
            return Response(
                {"detail": f"Cannot cancel booking with status '{booking.status}'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        booking.status = Booking.BookingStatus.CANCELLED
        booking.save(update_fields=['status', 'updated_at'])
        return Response({"message": "Booking has been cancelled."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='simulate-dispatch', permission_classes=[AllowAny])
    def simulate_dispatch(self, request, pk=None):
        booking = self.get_object()
        count = dispatch_booking_to_vendors(booking)
        return Response({
            "message": f"Dispatched booking {booking.id} to {count} eligible vendors.",
            "booking_status": booking.status,
            "dispatched_vendors_count": count
        })


class VendorAcceptBookingView(APIView):
    """
    First-accept handler: Atomically accepts a dispatched booking.
    The first vendor to accept locks the booking; subsequent vendors get a 409 Conflict.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        request=VendorActionSerializer,
        responses={
            200: OpenApiResponse(description="Booking successfully assigned to vendor"),
            404: OpenApiResponse(description="Vendor or Booking not found"),
            409: OpenApiResponse(description="Booking already accepted by another vendor"),
        },
        description="Vendor accepts a dispatched booking. First-to-accept wins."
    )
    def post(self, request, booking_id):
        serializer = VendorActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vendor_id = serializer.validated_data['vendor_id']

        try:
            vendor = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            return Response({"detail": "Vendor not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            booking = accept_booking(booking_id=booking_id, vendor=vendor)
            return Response({
                "message": f"Congratulations! Booking has been assigned to {vendor.name}.",
                "booking": BookingDetailSerializer(booking).data
            }, status=status.HTTP_200_OK)
        except BookingAlreadyAcceptedError as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)
        except BookingInvalidStateError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Booking.DoesNotExist:
            return Response({"detail": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)


class VendorRejectBookingView(APIView):
    """
    Allows a vendor to decline/reject a dispatched booking request.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        request=VendorActionSerializer,
        responses={200: OpenApiResponse(description="Booking request successfully declined")},
        description="Vendor rejects a dispatched booking."
    )
    def post(self, request, booking_id):
        serializer = VendorActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vendor_id = serializer.validated_data['vendor_id']

        try:
            vendor = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            return Response({"detail": "Vendor not found."}, status=status.HTTP_404_NOT_FOUND)

        reject_booking(booking_id=booking_id, vendor=vendor)
        return Response({"message": "Booking request declined."}, status=status.HTTP_200_OK)
