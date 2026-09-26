import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, phone_number, full_name="User", password=None, **extra_fields):
        if not phone_number:
            raise ValueError("The Phone Number is required")
        user = self.model(phone_number=phone_number, full_name=full_name, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, full_name="Admin", password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('phone_verified_at', timezone.now())

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone_number, full_name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=150)
    email = models.EmailField(max_length=255, unique=True, null=True, blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, unique=True)
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    avatar_url = models.URLField(max_length=1024, null=True, blank=True)
    origin_state = models.CharField(max_length=100, null=True, blank=True)
    origin_city = models.CharField(max_length=100, null=True, blank=True)
    gotra = models.CharField(max_length=100, null=True, blank=True)
    mother_tongue = models.CharField(max_length=50, default='hi')
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.full_name} ({self.phone_number})"


class UserAddress(models.Model):
    class AddressType(models.TextChoices):
        HOME = 'HOME', 'Home'
        OFFICE = 'OFFICE', 'Office'
        OTHER = 'OTHER', 'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=32, choices=AddressType.choices, default=AddressType.HOME)
    custom_title = models.CharField(max_length=100, null=True, blank=True)
    flat_house_building = models.CharField(max_length=255)
    street_area_locality = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    landmark = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_addresses'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.address_type}: {self.flat_house_building}, {self.city}"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Ensure other addresses of this user are not default
            UserAddress.objects.filter(user=self.user, is_default=True).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)


class UserPhoneUpdateOTP(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phone_otps')
    new_phone_number = models.CharField(max_length=20)
    otp_hash = models.CharField(max_length=255)
    attempts_count = models.PositiveSmallIntegerField(default=0)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_phone_update_otps'


class PhoneAuthOTP(models.Model):
    """
    Handles Login/Signup OTP requests before a user record is verified.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=20)
    otp_hash = models.CharField(max_length=255)
    attempts_count = models.PositiveSmallIntegerField(default=0)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'phone_auth_otps'
        ordering = ['-created_at']


class UserDevice(models.Model):
    """
    Stores customer FCM tokens to notify when vendor/pandit is assigned.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    fcm_token = models.CharField(max_length=512)
    device_type = models.CharField(max_length=32, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_devices'
        unique_together = ('user', 'fcm_token')
