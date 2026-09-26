from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from .models import Category, Service
from .serializers import (
    CategoryTreeSerializer,
    ServiceListSerializer,
    ServiceDetailSerializer
)
from apps.accounts.serializers import UserAddressSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True).prefetch_related('subcategories', 'services')
    serializer_class = CategoryTreeSerializer
    lookup_field = 'slug'
    permission_classes = [AllowAny]

    def get_queryset(self):
        # By default, list top-level parent categories
        if self.action == 'list':
            return Category.objects.filter(is_active=True, parent__isnull=True).prefetch_related('subcategories', 'services')
        return Category.objects.filter(is_active=True).prefetch_related('subcategories', 'services')

    @action(detail=True, methods=['get'], url_path='services')
    def services(self, request, slug=None):
        category = self.get_object()
        # Include services directly in this category or in any of its subcategories
        sub_cat_ids = category.subcategories.values_list('id', flat=True)
        all_cat_ids = [category.id] + list(sub_cat_ids)
        services = Service.objects.filter(category_id__in=all_cat_ids, is_active=True)
        serializer = ServiceListSerializer(services, many=True)
        return Response(serializer.data)


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.filter(is_active=True).select_related('category').prefetch_related('samagri_items', 'tags')
    lookup_field = 'slug'
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ServiceDetailSerializer
        return ServiceListSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(name='category', description='Filter by Category Slug', required=False, type=str),
            OpenApiParameter(name='popular', description='Filter popular services (true/false)', required=False, type=bool),
            OpenApiParameter(name='search', description='Search by service name or about', required=False, type=str),
        ]
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        category_slug = request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(
                Q(category__slug=category_slug) | Q(category__parent__slug=category_slug)
            )

        is_popular = request.query_params.get('popular')
        if is_popular and is_popular.lower() in ('true', '1'):
            queryset = queryset.filter(is_popular=True)

        search_query = request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | Q(about__icontains=search_query)
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='popular')
    def popular(self, request):
        popular_services = self.get_queryset().filter(is_popular=True)[:12]
        serializer = ServiceListSerializer(popular_services, many=True)
        return Response(serializer.data)


class HomeFeedView(APIView):
    """
    Unified Airbnb-style home page aggregator:
    - Pooja & Service Categories hierarchy with icons
    - Popular pooja & service tiles
    - Popular artis (from devotional module)
    - Horoscopes (from devotional module)
    - Customer's active/default address (if authenticated)
    """
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: OpenApiResponse(description="Consolidated home feed containing categories hierarchy, popular services, popular artis, and horoscopes.")},
        description="Fetch complete home page content (categories, popular poojas, artis, horoscopes, user default address) in one call."
    )
    def get(self, request):
        # 1. Categories
        categories = Category.objects.filter(is_active=True, parent__isnull=True).prefetch_related('subcategories')
        categories_data = CategoryTreeSerializer(categories, many=True).data

        # 2. Popular Services
        popular_services = Service.objects.filter(is_active=True, is_popular=True)[:10]
        services_data = ServiceListSerializer(popular_services, many=True).data

        # 3. Artis (Devotional)
        artis_data = []
        try:
            from apps.devotional.models import Arti
            from apps.devotional.serializers import ArtiListSerializer
            popular_artis = Arti.objects.filter(is_popular=True)[:6]
            artis_data = ArtiListSerializer(popular_artis, many=True).data
        except Exception:
            pass

        # 4. Horoscopes (Devotional)
        horoscopes_data = []
        try:
            from apps.devotional.models import Horoscope
            from apps.devotional.serializers import HoroscopeSerializer
            import datetime
            today = datetime.date.today()
            daily_horoscopes = Horoscope.objects.filter(period_type=Horoscope.PeriodType.DAILY, period_date=today)
            if not daily_horoscopes.exists():
                # Fallback to latest available daily horoscopes
                daily_horoscopes = Horoscope.objects.filter(period_type=Horoscope.PeriodType.DAILY).order_by('-period_date')[:12]
            horoscopes_data = HoroscopeSerializer(daily_horoscopes, many=True).data
        except Exception:
            pass

        # 5. Default address (if logged in)
        default_address = None
        if request.user.is_authenticated:
            addr = request.user.addresses.filter(is_default=True).first() or request.user.addresses.first()
            if addr:
                default_address = UserAddressSerializer(addr).data

        return Response({
            "categories": categories_data,
            "popular_services": services_data,
            "popular_artis": artis_data,
            "daily_horoscopes": horoscopes_data,
            "selected_address": default_address,
        }, status=status.HTTP_200_OK)
