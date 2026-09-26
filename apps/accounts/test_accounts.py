from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User, UserAddress, UserDevice, PhoneAuthOTP


class AccountsAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.phone = "+919876543210"

    def test_request_and_verify_otp_flow(self):
        # 1. Request OTP
        req_res = self.client.post('/api/v1/auth/request-otp/', {'phone_number': self.phone})
        self.assertEqual(req_res.status_code, status.HTTP_200_OK)
        self.assertIn('dev_otp', req_res.data)
        dev_otp = req_res.data['dev_otp']

        # 2. Verify OTP
        verify_res = self.client.post('/api/v1/auth/verify-otp/', {
            'phone_number': self.phone,
            'otp_code': dev_otp,
            'full_name': 'Test Devotee'
        })
        self.assertEqual(verify_res.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', verify_res.data)
        self.assertIn('access', verify_res.data['tokens'])

        token = verify_res.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # 3. Fetch User Profile
        profile_res = self.client.get('/api/v1/users/me/')
        self.assertEqual(profile_res.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_res.data['phone_number'], self.phone)
        self.assertEqual(profile_res.data['full_name'], 'Test Devotee')

        # 4. Update Profile with Origin and Gotra
        patch_res = self.client.patch('/api/v1/users/me/', {
            'origin_state': 'Uttar Pradesh',
            'origin_city': 'Varanasi',
            'gotra': 'Kashyap'
        })
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_res.data['origin_state'], 'Uttar Pradesh')
        self.assertEqual(patch_res.data['gotra'], 'Kashyap')

    def test_user_address_management_and_default(self):
        user = User.objects.create_user(phone_number="+919999988888", full_name="Address Tester")
        self.client.force_authenticate(user=user)

        # Create address 1
        addr1_res = self.client.post('/api/v1/users/addresses/', {
            'address_type': 'HOME',
            'flat_house_building': 'Flat 101',
            'street_area_locality': 'Sector 15',
            'city': 'Noida',
            'state': 'UP',
            'postal_code': '201301',
            'latitude': 28.5800,
            'longitude': 77.3100
        })
        self.assertEqual(addr1_res.status_code, status.HTTP_201_CREATED)
        addr1_id = addr1_res.data['id']
        self.assertTrue(addr1_res.data['is_default'])  # First address auto-defaults to True

        # Create address 2
        addr2_res = self.client.post('/api/v1/users/addresses/', {
            'address_type': 'OFFICE',
            'flat_house_building': 'Tower 4',
            'street_area_locality': 'Cyber City',
            'city': 'Gurugram',
            'state': 'Haryana',
            'postal_code': '122002',
            'latitude': 28.4900,
            'longitude': 77.0900
        })
        self.assertEqual(addr2_res.status_code, status.HTTP_201_CREATED)
        addr2_id = addr2_res.data['id']
        self.assertFalse(addr2_res.data['is_default'])

        # Set address 2 as default
        set_def_res = self.client.post(f'/api/v1/users/addresses/{addr2_id}/set-default/')
        self.assertEqual(set_def_res.status_code, status.HTTP_200_OK)
        self.assertTrue(set_def_res.data['is_default'])

        # Verify address 1 is no longer default
        addr1_check = UserAddress.objects.get(id=addr1_id)
        self.assertFalse(addr1_check.is_default)

    def test_user_device_registration(self):
        user = User.objects.create_user(phone_number="+919777766666", full_name="Device Tester")
        self.client.force_authenticate(user=user)

        res = self.client.post('/api/v1/users/device-token/', {
            'fcm_token': 'test_fcm_token_123',
            'device_type': 'react_native_ios'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(UserDevice.objects.filter(user=user).count(), 1)
