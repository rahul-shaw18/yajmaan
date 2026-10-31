import uuid
from django.db import models


class VendorOnboardingApplication(models.Model):
    class Status(models.TextChoices):
        PENDING_APPROVAL = 'PENDING_APPROVAL', 'Pending Approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(max_length=255, null=True, blank=True)
    origin_state = models.CharField(max_length=100, null=True, blank=True)
    origin_city = models.CharField(max_length=100, null=True, blank=True)
    qualification = models.TextField(null=True, blank=True)
    
    # KYC & Verification
    id_proof_type = models.CharField(max_length=50, null=True, blank=True)
    id_proof_number = models.CharField(max_length=100, null=True, blank=True)
    id_proof_document_url = models.URLField(max_length=1024, null=True, blank=True)
    pan_card_number = models.CharField(max_length=30, null=True, blank=True)
    pan_card_document_url = models.URLField(max_length=1024, null=True, blank=True)
    bank_account_number = models.CharField(max_length=50, null=True, blank=True)
    bank_ifsc_code = models.CharField(max_length=20, null=True, blank=True)
    bank_beneficiary_name = models.CharField(max_length=150, null=True, blank=True)
    
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING_APPROVAL)
    rejection_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'vendor_onboarding_applications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.status})"


class Vendor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    onboarding_application = models.OneToOneField(
        VendorOnboardingApplication,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='vendor_profile',
        db_column='onboarding_application_id'
    )
    categories = models.ManyToManyField(
        'catalog.Category',
        blank=True,
        related_name='vendors',
        db_table='vendor_categories'
    )
    name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(max_length=255, unique=True, null=True, blank=True)
    origin_state = models.CharField(max_length=100, null=True, blank=True)
    origin_city = models.CharField(max_length=100, null=True, blank=True)
    qualification = models.TextField(null=True, blank=True)
    experience_years = models.PositiveSmallIntegerField(default=5)
    rating_average = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    reviews_count = models.PositiveIntegerField(default=0)
    
    # Coordinates & Service Radius for dispatch
    current_latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    location_updated_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp of latest device GPS heartbeat")
    service_radius_km = models.DecimalField(max_digits=5, decimal_places=2, default=15.0)
    
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    is_on_duty = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'vendors'
        ordering = ['-rating_average', 'name']

    def __str__(self):
        return f"{self.name} - {self.origin_city or 'Unknown'}, {self.origin_state or ''}"


class VendorLocationHistory(models.Model):
    """
    Logs 30-minute interval GPS location pings from on-duty vendor devices.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='location_history',
        db_column='vendor_id'
    )
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vendor_location_history'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vendor.name} @ ({self.latitude}, {self.longitude}) at {self.created_at}"


class VendorDevice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='devices',
        db_column='vendor_id'
    )
    fcm_token = models.CharField(max_length=512)
    device_type = models.CharField(max_length=32, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'vendor_devices'
        unique_together = ('vendor', 'fcm_token')

    def __str__(self):
        return f"{self.vendor.name} device ({self.fcm_token[:15]}...)"
