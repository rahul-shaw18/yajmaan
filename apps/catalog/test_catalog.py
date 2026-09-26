from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.catalog.models import Category, Service, PoojaSamagriItem


class CatalogAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create parent and subcategory
        self.parent_cat = Category.objects.create(name="Home & Property", slug="home-property", display_order=1)
        self.sub_cat = Category.objects.create(name="Griha Pravesh", slug="griha-pravesh", parent=self.parent_cat, display_order=1)

        # Create service
        self.service = Service.objects.create(
            category=self.sub_cat,
            name="Griha Pravesh Pooja",
            slug="griha-pravesh-pooja",
            banner_image_url="https://example.com/banner.jpg",
            duration_text="2.5 - 3 Hours",
            duration_minutes_min=150,
            duration_minutes_max=180,
            vendors_required=1,
            rating_average=4.9,
            reviews_count=50,
            price_without_samagri=2500.00,
            price_with_samagri=4200.00,
            about="Sacred housewarming pooja.",
            meta={"benefits": [{"title": "Peace", "description": "Brings prosperity"}]},
            is_popular=True
        )

        PoojaSamagriItem.objects.create(
            service=self.service,
            item_name="Desi Cow Ghee",
            quantity="500g",
            is_included_by_default=True
        )

    def test_category_tree_endpoint(self):
        res = self.client.get('/api/v1/catalog/categories/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Check parent category contains subcategories
        found = False
        for cat in res.data['results']:
            if cat['slug'] == 'home-property':
                found = True
                self.assertEqual(len(cat['subcategories']), 1)
                self.assertEqual(cat['subcategories'][0]['slug'], 'griha-pravesh')
        self.assertTrue(found)

    def test_service_detail_endpoint(self):
        res = self.client.get(f'/api/v1/catalog/services/{self.service.slug}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], "Griha Pravesh Pooja")
        self.assertEqual(float(res.data['price_without_samagri']), 2500.00)
        self.assertEqual(float(res.data['price_with_samagri']), 4200.00)
        self.assertEqual(len(res.data['samagri_items']), 1)
        self.assertEqual(res.data['samagri_items'][0]['item_name'], "Desi Cow Ghee")
        self.assertIn("benefits", res.data['meta'])

    def test_home_feed_endpoint(self):
        res = self.client.get('/api/v1/home/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('categories', res.data)
        self.assertIn('popular_services', res.data)
        self.assertTrue(len(res.data['categories']) >= 1)
        self.assertTrue(len(res.data['popular_services']) >= 1)
