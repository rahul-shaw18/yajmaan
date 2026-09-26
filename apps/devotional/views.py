import datetime
from django.db.models import Q
from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from .models import Arti, Horoscope
from .serializers import (
    ArtiListSerializer,
    ArtiDetailSerializer,
    HoroscopeSerializer
)


class ArtiViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Arti.objects.all().order_by('display_order', 'title')
    lookup_field = 'slug'
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ArtiDetailSerializer
        return ArtiListSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(name='popular', description='Filter popular artis (true/false)', required=False, type=bool),
            OpenApiParameter(name='deity', description='Filter by deity name (e.g. Ganesh, Shiva, Lakshmi)', required=False, type=str),
        ]
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        is_popular = request.query_params.get('popular')
        if is_popular and is_popular.lower() in ('true', '1'):
            queryset = queryset.filter(is_popular=True)

        deity = request.query_params.get('deity')
        if deity:
            queryset = queryset.filter(deity__icontains=deity)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class HoroscopeListView(generics.ListAPIView):
    serializer_class = HoroscopeSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='type', description='Period type: DAILY or MONTHLY', required=False, type=str),
            OpenApiParameter(name='sign', description='Filter by zodiac sign (e.g. Aries, Taurus, etc.)', required=False, type=str),
        ]
    )
    def get_queryset(self):
        queryset = Horoscope.objects.all()
        period_type = self.request.query_params.get('type')
        if period_type:
            queryset = queryset.filter(period_type=period_type.upper())

        sign = self.request.query_params.get('sign')
        if sign:
            queryset = queryset.filter(zodiac_sign__iexact=sign)

        return queryset


class ZodiacSignHoroscopeView(APIView):
    """
    Returns today's horoscope and next month's horoscope for a specific zodiac sign.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: OpenApiResponse(description="Returns daily and monthly horoscope for sign")},
        description="Retrieve current daily and upcoming monthly horoscope for a given zodiac sign."
    )
    def get(self, request, sign):
        today = datetime.date.today()

        daily = Horoscope.objects.filter(
            zodiac_sign__iexact=sign,
            period_type=Horoscope.PeriodType.DAILY
        ).order_by('-period_date').first()

        monthly = Horoscope.objects.filter(
            zodiac_sign__iexact=sign,
            period_type=Horoscope.PeriodType.MONTHLY
        ).order_by('-period_date').first()

        return Response({
            "zodiac_sign": sign.capitalize(),
            "daily_horoscope": HoroscopeSerializer(daily).data if daily else None,
            "monthly_horoscope": HoroscopeSerializer(monthly).data if monthly else None,
        }, status=status.HTTP_200_OK)
