from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ServiceViewSet

router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='categories')
router.register('services', ServiceViewSet, basename='services')
router.register('poojas', ServiceViewSet, basename='poojas')  # <-- Aliases /poojas/ to ServiceViewSet

urlpatterns = [
    path('', include(router.urls)),
]
