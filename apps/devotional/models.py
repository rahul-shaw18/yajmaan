import uuid
from django.db import models


class Arti(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    deity = models.CharField(max_length=150, null=True, blank=True)
    lyrics_text = models.TextField(help_text="Full Hindi/Sanskrit lyrics text")
    audio_url = models.URLField(max_length=1024, null=True, blank=True, help_text="Direct URL to streaming MP3 audio")
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    thumbnail_url = models.URLField(max_length=1024, null=True, blank=True)
    is_popular = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'artis'
        ordering = ['display_order', 'title']

    def __str__(self):
        return self.title


class Horoscope(models.Model):
    class PeriodType(models.TextChoices):
        DAILY = 'DAILY', 'Daily'
        MONTHLY = 'MONTHLY', 'Monthly'

    ZODIAC_SIGNS = [
        ('Aries', 'Aries (Mesh)'),
        ('Taurus', 'Taurus (Vrishabh)'),
        ('Gemini', 'Gemini (Mithun)'),
        ('Cancer', 'Cancer (Kark)'),
        ('Leo', 'Leo (Singh)'),
        ('Virgo', 'Virgo (Kanya)'),
        ('Libra', 'Libra (Tula)'),
        ('Scorpio', 'Scorpio (Vrishchik)'),
        ('Sagittarius', 'Sagittarius (Dhanu)'),
        ('Capricorn', 'Capricorn (Makar)'),
        ('Aquarius', 'Aquarius (Kumbh)'),
        ('Pisces', 'Pisces (Meen)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    zodiac_sign = models.CharField(max_length=32, choices=ZODIAC_SIGNS)
    period_type = models.CharField(max_length=16, choices=PeriodType.choices, default=PeriodType.DAILY)
    period_date = models.DateField(help_text="Date for daily or first day of month for monthly")
    prediction_text = models.TextField()
    lucky_color = models.CharField(max_length=50, null=True, blank=True)
    lucky_number = models.PositiveSmallIntegerField(null=True, blank=True)
    icon_url = models.URLField(max_length=1024, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'horoscopes'
        ordering = ['period_date', 'zodiac_sign']
        unique_together = ('zodiac_sign', 'period_type', 'period_date')

    def __str__(self):
        return f"{self.zodiac_sign} - {self.period_type} ({self.period_date})"
