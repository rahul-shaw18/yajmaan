from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BookingViewSet,
    VendorAcceptBookingView,
    VendorRejectBookingView
)

router = DefaultRouter()
router.register('', BookingViewSet, basename='bookings')

urlpatterns = [
    path('<uuid:booking_id>/accept/', VendorAcceptBookingView.as_view(), name='vendor-accept-booking'),
    path('<uuid:booking_id>/reject/', VendorRejectBookingView.as_view(), name='vendor-reject-booking'),
    path('', include(router.urls)),
]
