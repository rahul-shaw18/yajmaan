from django.urls import path
from .views import (
    VendorOnboardingView,
    VendorListView,
    VendorDetailView,
    VendorDeviceView,
    VendorLocationView,
    VendorAvailableJobsView,
    VendorDutyView
)

urlpatterns = [
    path('', VendorListView.as_view(), name='vendor-list'),
    path('<uuid:id>/', VendorDetailView.as_view(), name='vendor-detail'),
    path('onboarding/', VendorOnboardingView.as_view(), name='vendor-onboarding'),
    path('device-token/', VendorDeviceView.as_view(), name='vendor-device-token'),
    path('location/', VendorLocationView.as_view(), name='vendor-location-update'),
    path('duty/', VendorDutyView.as_view(), name='vendor-duty-toggle'),
    path('available-jobs/', VendorAvailableJobsView.as_view(), name='vendor-available-jobs'),
]

