from rest_framework import serializers
from .models import Category, Tag, Service, PoojaSamagriItem


class PoojaSamagriItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PoojaSamagriItem
        fields = ['id', 'item_name', 'quantity', 'is_included_by_default']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class SubcategorySerializer(serializers.ModelSerializer):
    services_count = serializers.IntegerField(source='services.count', read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon_url', 'display_order', 'services_count']


class CategoryTreeSerializer(serializers.ModelSerializer):
    subcategories = SubcategorySerializer(many=True, read_only=True)
    services_count = serializers.IntegerField(source='services.count', read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon_url', 'display_order', 'services_count', 'subcategories']


class ServiceListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)

    class Meta:
        model = Service
        fields = [
            'id', 'category_id', 'category_name', 'category_slug',
            'name', 'slug', 'banner_image_url', 'thumbnail_url',
            'duration_text', 'duration_minutes_min', 'duration_minutes_max',
            'vendors_required', 'rating_average', 'reviews_count',
            'price_without_samagri', 'price_with_samagri',
            'is_popular', 'is_active'
        ]


class ServiceDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    samagri_items = PoojaSamagriItemSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Service
        fields = [
            'id', 'category_id', 'category_name', 'category_slug',
            'name', 'slug', 'banner_image_url', 'thumbnail_url',
            'duration_text', 'duration_minutes_min', 'duration_minutes_max',
            'vendors_required', 'rating_average', 'reviews_count',
            'about', 'price_without_samagri', 'price_with_samagri',
            'meta', 'samagri_items', 'tags', 'is_popular', 'is_active',
            'created_at', 'updated_at'
        ]
