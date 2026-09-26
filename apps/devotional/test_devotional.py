import datetime
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.devotional.models import Arti, Horoscope


class DevotionalAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create Arti
        self.arti = Arti.objects.create(
            title="Jai Ganesh Deva",
            slug="jai-ganesh-deva",
            deity="Lord Ganesha",
            lyrics_text="जय गणेश, जय गणेश, जय गणेश देवा।",
            audio_url="https://example.com/ganesh.mp3",
            duration_seconds=240,
            is_popular=True,
            display_order=1
        )

        # Create Horoscope
        today = datetime.date.today()
        self.horoscope_daily = Horoscope.objects.create(
            zodiac_sign="Aries",
            period_type=Horoscope.PeriodType.DAILY,
            period_date=today,
            prediction_text="Favorable day for new beginnings.",
            lucky_color="Red",
            lucky_number=9
        )
        self.horoscope_monthly = Horoscope.objects.create(
            zodiac_sign="Aries",
            period_type=Horoscope.PeriodType.MONTHLY,
            period_date=today.replace(day=1),
            prediction_text="Great month ahead.",
            lucky_color="Red",
            lucky_number=9
        )

    def test_arti_list_and_detail(self):
        # List
        res_list = self.client.get('/api/v1/devotional/artis/')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertTrue(len(res_list.data['results']) >= 1)

        # Detail with lyrics & audio
        res_detail = self.client.get(f'/api/v1/devotional/artis/{self.arti.slug}/')
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(res_detail.data['title'], "Jai Ganesh Deva")
        self.assertIn("जय गणेश देवा", res_detail.data['lyrics_text'])
        self.assertEqual(res_detail.data['audio_url'], "https://example.com/ganesh.mp3")

    def test_horoscope_by_sign(self):
        res = self.client.get('/api/v1/devotional/horoscopes/Aries/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['zodiac_sign'], "Aries")
        self.assertIsNotNone(res.data['daily_horoscope'])
        self.assertIsNotNone(res.data['monthly_horoscope'])
        self.assertEqual(res.data['daily_horoscope']['lucky_color'], "Red")
