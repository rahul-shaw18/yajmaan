from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArtiViewSet, HoroscopeListView, ZodiacSignHoroscopeView

router = DefaultRouter()
router.register('artis', ArtiViewSet, basename='artis')
router.register('arti', ArtiViewSet, basename='arti')  # <-- Aliases /arti/ to ArtiViewSet

urlpatterns = [
    path('horoscopes/', HoroscopeListView.as_view(), name='horoscope-list'),
    path('horoscopes/<str:sign>/', ZodiacSignHoroscopeView.as_view(), name='zodiac-horoscope'),
    path('', include(router.urls)),
]
