from rest_framework import serializers
from .models import Arti, Horoscope


class ArtiListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Arti
        fields = ['id', 'title', 'slug', 'deity', 'thumbnail_url', 'duration_seconds', 'is_popular']


class ArtiDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Arti
        fields = [
            'id', 'title', 'slug', 'deity', 'lyrics_text', 'audio_url',
            'thumbnail_url', 'duration_seconds', 'is_popular', 'display_order',
            'created_at'
        ]


class HoroscopeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Horoscope
        fields = [
            'id', 'zodiac_sign', 'period_type', 'period_date',
            'prediction_text', 'lucky_color', 'lucky_number',
            'icon_url', 'created_at'
        ]
