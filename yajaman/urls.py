from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)
from apps.catalog.views import HomeFeedView

urlpatterns = [
    path('admin/', admin.site.urls),

    # OpenAPI 3.0 Documentation & Swagger UI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Yajaman REST APIs v1
    path('api/v1/auth/', include('apps.accounts.auth_urls')),
    path('api/v1/users/', include('apps.accounts.user_urls')),
    path('api/v1/catalog/', include('apps.catalog.urls')),
    path('api/v1/vendors/', include('apps.vendors.urls')),
    path('api/v1/bookings/', include('apps.bookings.urls')),
    path('api/v1/devotional/', include('apps.devotional.urls')),
    path('api/v1/home/', HomeFeedView.as_view(), name='home-feed'),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
