import datetime
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User, UserAddress, UserDevice
from apps.catalog.models import Category, Service
from apps.vendors.models import Vendor, VendorDevice
from apps.bookings.models import Booking, BookingDispatchLog, Payment
from apps.bookings.dispatch import find_eligible_vendors, accept_booking, BookingAlreadyAcceptedError


class BookingsAndDispatchEngineTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. Customer
        self.customer = User.objects.create_user(
            phone_number="+919876543210",
            full_name="Rajesh Devotee",
            origin_state="Uttar Pradesh",
            origin_city="Varanasi",
            gotra="Vashishta"
        )
        self.client.force_authenticate(user=self.customer)

        # Customer Device
        UserDevice.objects.create(
            user=self.customer,
            fcm_token="customer_fcm_token_xyz"
        )

        # Customer Address (Noida, Sector 62: 28.6200, 77.3600)
        self.address = UserAddress.objects.create(
            user=self.customer,
            address_type=UserAddress.AddressType.HOME,
            flat_house_building="A-101",
            street_area_locality="Sector 62",
            city="Noida",
            state="Uttar Pradesh",
            postal_code="201309",
            latitude=28.6200,
            longitude=77.3600,
            is_default=True
        )

        # 2. Service
        self.category = Category.objects.create(name="Havan", slug="havan")
        self.service = Service.objects.create(
            category=self.category,
            name="Ganesh Havan",
            slug="ganesh-havan",
            banner_image_url="https://example.com/havan.jpg",
            duration_text="1 Hour",
            duration_minutes_min=60,
            duration_minutes_max=90,
            vendors_required=1,
            price_without_samagri=1500.00,
            price_with_samagri=2500.00,
            about="Auspicious Ganesha Havan",
        )

        # 3. Vendors
        # Vendor 1: Close (Noida, ~2.2 km), matching origin (UP, Varanasi) -> On duty, initial 5km match
        self.vendor_up = Vendor.objects.create(
            name="Pandit Varanasi Vale",
            phone_number="+919811111111",
            origin_state="Uttar Pradesh",
            origin_city="Varanasi",
            qualification="Acharya",
            current_latitude=28.6300,
            current_longitude=77.3800,
            service_radius_km=15.0,
            is_active=True,
            is_available=True,
            is_on_duty=True,
            rating_average=4.9
        )
        self.vendor_up.categories.add(self.category)
        VendorDevice.objects.create(vendor=self.vendor_up, fcm_token="vendor_1_fcm_token")

        # Vendor 2: In expansion radius (~6.5 km away), on duty
        self.vendor_mid = Vendor.objects.create(
            name="Pandit Greater Noida Vale",
            phone_number="+919822222222",
            origin_state="Bihar",
            origin_city="Darbhanga",
            qualification="Shastri",
            current_latitude=28.6500,
            current_longitude=77.4100,
            service_radius_km=20.0,
            is_active=True,
            is_available=True,
            is_on_duty=True,
            rating_average=4.8
        )
        self.vendor_mid.categories.add(self.category)
        VendorDevice.objects.create(vendor=self.vendor_mid, fcm_token="vendor_2_fcm_token")

        # Vendor 3: Too far away (Gurugram: ~40 km away) -> Ineligible
        self.vendor_far = Vendor.objects.create(
            name="Pandit Far Away",
            phone_number="+919833333333",
            origin_state="Uttar Pradesh",
            origin_city="Varanasi",
            current_latitude=28.4595,
            current_longitude=77.0266,
            service_radius_km=15.0,
            is_active=True,
            is_available=True,
            is_on_duty=True
        )
        self.vendor_far.categories.add(self.category)


    def test_booking_creation_and_dispatch_engine(self):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        res = self.client.post('/api/v1/bookings/', {
            'service_id': str(self.service.id),
            'address_id': str(self.address.id),
            'pricing_variant': 'WITH_SAMAGRI',
            'preferred_date': str(tomorrow),
            'preferred_time_slot': '09:00 AM - 11:00 AM',
            'payment_mode': 'PAY_NOW'
        })

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        booking_id = res.data['id']
        booking = Booking.objects.get(id=booking_id)

        # Verify price matches with_samagri
        self.assertEqual(float(booking.total_price), 2500.00)
        self.assertEqual(booking.status, Booking.BookingStatus.SEARCHING_VENDOR)

        # Verify payment created
        self.assertEqual(booking.payments.count(), 1)
        self.assertEqual(booking.payments.first().payment_mode, Payment.PaymentMode.PAY_NOW)
        self.assertEqual(booking.payments.first().status, Payment.PaymentStatus.COMPLETED)

        # Verify dispatch logs: Only initial 5km on-duty vendor matched first
        dispatched_vendor_ids = list(booking.dispatch_logs.values_list('vendor_id', flat=True))
        self.assertIn(self.vendor_up.id, dispatched_vendor_ids)
        self.assertNotIn(self.vendor_far.id, dispatched_vendor_ids)  # Far vendor excluded

        # Test find_eligible_vendors priority ranking (5km radius match)
        ranked = find_eligible_vendors(booking)
        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0]['vendor'].id, self.vendor_up.id)

    def test_off_duty_vendor_exclusion_and_radius_expansion(self):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        booking = Booking.objects.create(
            user=self.customer,
            service=self.service,
            address=self.address,
            pricing_variant=Booking.PricingVariant.WITH_SAMAGRI,
            total_price=2500.00,
            preferred_date=tomorrow,
            preferred_time_slot='10:00 AM',
            snapshot_booking_address={"city": "Noida"},
            status=Booking.BookingStatus.SEARCHING_VENDOR
        )

        # 1. Turn close vendor off duty
        self.vendor_up.is_on_duty = False
        self.vendor_up.save()

        # 2. When searching eligible vendors, initial 5km has 0 vendors, so expansion loop expands to 7km and finds vendor_mid (~6.5 km away)
        ranked = find_eligible_vendors(booking)
        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0]['vendor'].id, self.vendor_mid.id)

    def test_no_vendor_available_when_all_off_duty_or_out_of_radius(self):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        booking = Booking.objects.create(
            user=self.customer,
            service=self.service,
            address=self.address,
            pricing_variant=Booking.PricingVariant.WITH_SAMAGRI,
            total_price=2500.00,
            preferred_date=tomorrow,
            preferred_time_slot='10:00 AM',
            snapshot_booking_address={"city": "Noida"},
            status=Booking.BookingStatus.SEARCHING_VENDOR
        )

        # Turn all vendors off duty
        Vendor.objects.all().update(is_on_duty=False)

        ranked = find_eligible_vendors(booking)
        self.assertEqual(len(ranked), 0)

        # Simulate dispatch API response
        res = self.client.post(f'/api/v1/bookings/{booking.id}/simulate-dispatch/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("No vendor available right now", res.data['message'])

    def test_first_accept_concurrency_and_race_condition(self):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        booking = Booking.objects.create(
            user=self.customer,
            service=self.service,
            address=self.address,
            pricing_variant=Booking.PricingVariant.WITH_SAMAGRI,
            total_price=2500.00,
            preferred_date=tomorrow,
            preferred_time_slot='10:00 AM',
            snapshot_booking_address={"city": "Noida"},
            status=Booking.BookingStatus.SEARCHING_VENDOR
        )

        BookingDispatchLog.objects.create(booking=booking, vendor=self.vendor_up, response_status='DISPATCHED')
        BookingDispatchLog.objects.create(booking=booking, vendor=self.vendor_mid, response_status='DISPATCHED')

        # 1. Vendor 1 accepts
        res1 = self.client.post(f'/api/v1/bookings/{booking.id}/accept/', {
            'vendor_id': str(self.vendor_up.id)
        })
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertIn("Congratulations", res1.data['message'])

        # Verify booking state
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.BookingStatus.ACCEPTED)
        self.assertEqual(booking.vendor, self.vendor_up)

        # Verify dispatch log for vendor 1 is ACCEPTED, other is EXPIRED
        self.assertEqual(BookingDispatchLog.objects.get(booking=booking, vendor=self.vendor_up).response_status, 'ACCEPTED')
        self.assertEqual(BookingDispatchLog.objects.get(booking=booking, vendor=self.vendor_mid).response_status, 'EXPIRED')

        # 2. Vendor 2 attempts to accept the SAME booking -> Must get 409 Conflict
        res2 = self.client.post(f'/api/v1/bookings/{booking.id}/accept/', {
            'vendor_id': str(self.vendor_mid.id)
        })
        self.assertEqual(res2.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("already been accepted", res2.data['detail'])

