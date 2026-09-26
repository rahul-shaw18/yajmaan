from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserProfileView,
    UserAddressViewSet,
    UserDeviceView,
    RequestPhoneUpdateView,
    VerifyPhoneUpdateView
)

router = DefaultRouter()
router.register('addresses', UserAddressViewSet, basename='user-addresses')

urlpatterns = [
    path('me/', UserProfileView.as_view(), name='user-profile'),
    path('device-token/', UserDeviceView.as_view(), name='user-device-token'),
    path('request-phone-update/', RequestPhoneUpdateView.as_view(), name='user-request-phone-update'),
    path('verify-phone-update/', VerifyPhoneUpdateView.as_view(), name='user-verify-phone-update'),
    path('', include(router.urls)),
]
