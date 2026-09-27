import os
import json
import logging
import datetime
import urllib.request
import urllib.error
from zoneinfo import ZoneInfo
from django.conf import settings
from django.core.cache import cache

from .models import Horoscope

logger = logging.getLogger(__name__)

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")

# Mapping of common sign names/Hindi names to canonical sign names
CANONICAL_ZODIAC_SIGNS = {
    'aries': 'Aries', 'mesh': 'Aries', 'mesha': 'Aries',
    'taurus': 'Taurus', 'vrishabh': 'Taurus', 'vrishabha': 'Taurus',
    'gemini': 'Gemini', 'mithun': 'Gemini', 'mithuna': 'Gemini',
    'cancer': 'Cancer', 'kark': 'Cancer', 'karka': 'Cancer',
    'leo': 'Leo', 'singh': 'Leo', 'simha': 'Leo',
    'virgo': 'Virgo', 'kanya': 'Virgo',
    'libra': 'Libra', 'tula': 'Libra',
    'scorpio': 'Scorpio', 'vrishchik': 'Scorpio', 'vrischika': 'Scorpio',
    'sagittarius': 'Sagittarius', 'dhanu': 'Sagittarius',
    'capricorn': 'Capricorn', 'makar': 'Capricorn', 'makara': 'Capricorn',
    'aquarius': 'Aquarius', 'kumbh': 'Aquarius', 'kumbha': 'Aquarius',
    'pisces': 'Pisces', 'meen': 'Pisces', 'meena': 'Pisces',
}

FALLBACK_PREDICTIONS = {
    'Aries': ("Dynamic opportunities present themselves today. Mars encourages bold action in professional ventures while Jupiter promotes harmony at home.", "Crimson Red", 9),
    'Taurus': ("Venus brings peaceful reflections and steady financial growth today. Focus on patience and nurturing key personal relationships.", "Lotus Pink", 6),
    'Gemini': ("Mercury enhances intellectual clarity and communicative prowess. Excellent time for creative ideas and spiritual discourse.", "Emerald Green", 5),
    'Cancer': ("The Moon supports intuitive decisions and family bonding. Dedicate quiet time for meditation and devotional peace.", "Pearl White", 2),
    'Leo': ("The Sun shines bright on your leadership qualities and career momentum. Cultivate generosity and warmth towards companions.", "Saffron Gold", 1),
    'Virgo': ("Attention to detail and practical endeavors yield rewarding results today. Health and mindfulness routines bring balance.", "Forest Green", 5),
    'Libra': ("Venus encourages aesthetic harmony and equitable partnerships. A peaceful and balanced approach brings auspicious outcomes.", "Sky Blue", 6),
    'Scorpio': ("Transformative insights and profound determination guide your decisions today. Channel energy into focused tasks.", "Maroon", 9),
    'Sagittarius': ("Jupiter opens doors to wisdom and philosophical clarity. Optimism and ethical pursuits attract favorable fortune.", "Haldi Yellow", 3),
    'Capricorn': ("Saturn rewards discipline and structured progress. Long-term goals receive steady support; maintain perseverance.", "Deep Navy", 8),
    'Aquarius': ("Innovative thinking and humanitarian impulses flourish today. Connect with peers who share high spiritual ideals.", "Electric Blue", 8),
    'Pisces': ("Deep empathy and spiritual connection enrich your day. Dedicate moments to prayer, music, and peaceful contemplation.", "Sea Green", 3),
}


def get_kolkata_now() -> datetime.datetime:
    """Return the current localized datetime in Asia/Kolkata timezone."""
    return datetime.datetime.now(KOLKATA_TZ)


def get_active_daily_date_and_ttl(now: datetime.datetime = None):
    """
    Computes the effective active date for the daily horoscope and cache TTL.
    Cutoff rule:
    - Before 11:00 PM (23:00) today: effective date is today, expires at 11:00 PM tonight.
    - At or after 11:00 PM (23:00) today: today's horoscope has expired! The effective
      date shifts to tomorrow, expiring at 11:00 PM tomorrow night.
    Returns: (active_date: datetime.date, ttl_seconds: int)
    """
    if now is None:
        now = get_kolkata_now()

    today = now.date()
    cutoff_today = datetime.datetime.combine(today, datetime.time(23, 0), tzinfo=KOLKATA_TZ)

    if now < cutoff_today:
        active_date = today
        expires_at = cutoff_today
    else:
        # After 11:00 PM, today's horoscope has expired; switch to tomorrow's reading
        active_date = today + datetime.timedelta(days=1)
        expires_at = datetime.datetime.combine(active_date, datetime.time(23, 0), tzinfo=KOLKATA_TZ)

    ttl_seconds = max(60, int((expires_at - now).total_seconds()))
    return active_date, ttl_seconds


def get_active_monthly_date_and_ttl(now: datetime.datetime = None):
    """
    Computes effective active date for monthly horoscope (1st of current month)
    and cache TTL until the start of next month.
    Returns: (active_month_date: datetime.date, ttl_seconds: int)
    """
    if now is None:
        now = get_kolkata_now()

    today = now.date()
    active_month_date = today.replace(day=1)

    if active_month_date.month == 12:
        next_month = active_month_date.replace(year=active_month_date.year + 1, month=1, day=1)
    else:
        next_month = active_month_date.replace(month=active_month_date.month + 1, day=1)

    expires_at = datetime.datetime.combine(next_month, datetime.time(0, 0), tzinfo=KOLKATA_TZ)
    ttl_seconds = max(60, int((expires_at - now).total_seconds()))
    return active_month_date, ttl_seconds


def prune_expired_horoscopes(now: datetime.datetime = None, force: bool = False):
    """
    Automatically deletes expired horoscopes from the database:
    - Daily horoscopes older than the active date (past 11:00 PM).
    - Monthly horoscopes older than the active month.
    Throttled to run at most once every 30 minutes unless forced.
    """
    if not force and cache.get('horoscope:last_pruned'):
        return

    if now is None:
        now = get_kolkata_now()

    active_daily_date, _ = get_active_daily_date_and_ttl(now)
    active_monthly_date, _ = get_active_monthly_date_and_ttl(now)

    try:
        # Delete daily horoscopes older than active date
        deleted_daily, _ = Horoscope.objects.filter(
            period_type=Horoscope.PeriodType.DAILY,
            period_date__lt=active_daily_date
        ).delete()

        # Delete monthly horoscopes older than current month
        deleted_monthly, _ = Horoscope.objects.filter(
            period_type=Horoscope.PeriodType.MONTHLY,
            period_date__lt=active_monthly_date
        ).delete()

        cache.set('horoscope:last_pruned', True, timeout=1800)
        if deleted_daily or deleted_monthly:
            logger.info("Pruned %d expired daily and %d monthly horoscopes", deleted_daily, deleted_monthly)
    except Exception as exc:
        logger.warning("Error pruning expired horoscopes: %s", exc)


def normalize_zodiac_sign(raw_sign: str) -> str:
    """Normalize zodiac sign input to canonical English name."""
    if not raw_sign:
        return 'Aries'
    cleaned = raw_sign.strip().lower()
    return CANONICAL_ZODIAC_SIGNS.get(cleaned, cleaned.capitalize())


def generate_horoscope_with_gemini(zodiac_sign: str, period_type: str, period_date: datetime.date) -> dict:
    """
    Calls Google Gemini API (gemini-3.8-flash) to generate an authentic
    Vedic astrology reading with prediction_text, lucky_color, and lucky_number.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', None) or os.getenv('GEMINI_API_KEY', None)

    if not api_key:
        logger.warning("GEMINI_API_KEY not set. Using astrological fallback for %s.", zodiac_sign)
        fallback_text, fallback_color, fallback_num = FALLBACK_PREDICTIONS.get(
            zodiac_sign, ("Auspicious day for growth and spiritual peace.", "Saffron", 7)
        )
        return {
            "prediction_text": fallback_text,
            "lucky_color": fallback_color,
            "lucky_number": fallback_num,
        }

    is_daily = (period_type == Horoscope.PeriodType.DAILY)
    date_display = period_date.strftime("%A, %d %B %Y") if is_daily else period_date.strftime("%B %Y")
    period_label = "Daily" if is_daily else "Monthly"

    prompt = f"""
You are a revered Vedic Astrologer providing an authentic {period_label} Horoscope (Rashifal) for the zodiac sign {zodiac_sign} (Rashi) for {date_display}.
Write an insightful, uplifting, and practical reading (3 to 4 sentences) covering:
1. Career, business, and financial guidance.
2. Relationships and family harmony.
3. Spiritual mindset and health recommendations.

Respond ONLY with a valid raw JSON object (no markdown code blocks, no backticks) with these exact keys:
{{
  "prediction_text": "3-4 sentences of Vedic prediction in graceful English",
  "lucky_color": "Auspicious color e.g. Saffron Yellow, Coral Red, Pearl White",
  "lucky_number": 7
}}
"""

    models_to_try = ['gemini-3.8-flash', 'gemini-3.5-flash-lite', 'gemini-3.5-flash']

    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                raw_text = result['candidates'][0]['content']['parts'][0]['text'].strip()

                # Clean any stray markdown fences if returned
                if raw_text.startswith("```"):
                    raw_text = raw_text.split("```")[1]
                    if raw_text.startswith("json"):
                        raw_text = raw_text[4:]
                    raw_text = raw_text.strip()

                data = json.loads(raw_text)
                return {
                    "prediction_text": data.get("prediction_text", "").strip(),
                    "lucky_color": data.get("lucky_color", "Saffron").strip(),
                    "lucky_number": int(data.get("lucky_number", 7)),
                }
        except urllib.error.HTTPError as http_err:
            logger.warning("Gemini %s returned HTTP %s: %s", model_name, http_err.code, http_err.reason)
            continue
        except Exception as exc:
            logger.warning("Gemini generation error with %s: %s", model_name, exc)
            continue

    # Graceful fallback if Gemini API is temporarily unavailable
    fallback_text, fallback_color, fallback_num = FALLBACK_PREDICTIONS.get(
        zodiac_sign, ("Auspicious day for growth, inner calm, and devotion.", "Saffron", 7)
    )
    return {
        "prediction_text": fallback_text,
        "lucky_color": fallback_color,
        "lucky_number": fallback_num,
    }


def get_or_create_horoscope(raw_sign: str, period_type: str = Horoscope.PeriodType.DAILY) -> Horoscope:
    """
    Multi-layer caching:
    Layer 1: Fast in-memory / Django Cache (TTL aligned with 11:00 PM cutoff).
    Layer 2: Supabase Database Table (`Horoscope` model).
    Layer 3: Gemini AI Generation on-demand.
    Also executes automatic pruning of records older than 11:00 PM.
    """
    now = get_kolkata_now()
    zodiac_sign = normalize_zodiac_sign(raw_sign)

    # 1. Determine active period date and cache TTL
    if period_type == Horoscope.PeriodType.MONTHLY:
        active_date, ttl_seconds = get_active_monthly_date_and_ttl(now)
        cache_key = f"horoscope:monthly:{zodiac_sign.lower()}:{active_date.isoformat()}"
    else:
        period_type = Horoscope.PeriodType.DAILY
        active_date, ttl_seconds = get_active_daily_date_and_ttl(now)
        cache_key = f"horoscope:daily:{zodiac_sign.lower()}:{active_date.isoformat()}"

    # 2. Layer 1: Check In-Memory Cache
    cached_obj = cache.get(cache_key)
    if cached_obj and isinstance(cached_obj, Horoscope):
        return cached_obj

    # 3. Layer 2: Check Database
    db_obj = Horoscope.objects.filter(
        zodiac_sign=zodiac_sign,
        period_type=period_type,
        period_date=active_date
    ).first()

    if db_obj:
        cache.set(cache_key, db_obj, timeout=ttl_seconds)
        # Periodic pruning of old records
        prune_expired_horoscopes(now)
        return db_obj

    # 4. Layer 3: Generate via Gemini AI
    ai_data = generate_horoscope_with_gemini(zodiac_sign, period_type, active_date)

    # Save to Database
    db_obj, _ = Horoscope.objects.update_or_create(
        zodiac_sign=zodiac_sign,
        period_type=period_type,
        period_date=active_date,
        defaults={
            "prediction_text": ai_data["prediction_text"],
            "lucky_color": ai_data.get("lucky_color", "Saffron"),
            "lucky_number": ai_data.get("lucky_number", 7),
        }
    )

    # Save to In-Memory Cache
    cache.set(cache_key, db_obj, timeout=ttl_seconds)

    # Prune any previous expired daily/monthly records
    prune_expired_horoscopes(now)

    return db_obj
