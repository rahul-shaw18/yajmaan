import uuid
from django.db import models


class Booking(models.Model):
    class BookingStatus(models.TextChoices):
        REQUESTED = 'REQUESTED', 'Requested'
        SEARCHING_VENDOR = 'SEARCHING_VENDOR', 'Searching Vendor'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    class PricingVariant(models.TextChoices):
        WITH_SAMAGRI = 'WITH_SAMAGRI', 'With Samagri'
        WITHOUT_SAMAGRI = 'WITHOUT_SAMAGRI', 'Without Samagri'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='bookings',
        db_column='user_id'
    )
    service = models.ForeignKey(
        'catalog.Service',
        on_delete=models.PROTECT,
        related_name='bookings',
        db_column='service_id'
    )
    vendor = models.ForeignKey(
        'vendors.Vendor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_bookings',
        db_column='vendor_id'
    )
    address = models.ForeignKey(
        'accounts.UserAddress',
        on_delete=models.PROTECT,
        related_name='bookings',
        db_column='address_id'
    )
    
    pricing_variant = models.CharField(max_length=32, choices=PricingVariant.choices)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    preferred_date = models.DateField()
    preferred_time_slot = models.CharField(max_length=64)
    
    # Immutable historical snapshots
    snapshot_booking_address = models.JSONField()
    snapshot_user_spiritual_origin = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=BookingStatus.choices, default=BookingStatus.REQUESTED)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bookings'
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking {str(self.id)[:8]} - {self.service.name} ({self.status})"


class BookingDispatchLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='dispatch_logs',
        db_column='booking_id'
    )
    vendor = models.ForeignKey(
        'vendors.Vendor',
        on_delete=models.CASCADE,
        related_name='received_dispatches',
        db_column='vendor_id'
    )
    fcm_message_id = models.CharField(max_length=255, null=True, blank=True)
    response_status = models.CharField(max_length=32, default='DISPATCHED')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'booking_dispatch_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"Dispatch {self.vendor.name} -> {self.booking.service.name} ({self.response_status})"


class Payment(models.Model):
    class PaymentMode(models.TextChoices):
        PAY_NOW = 'PAY_NOW', 'Pay Now'
        PAY_LATER = 'PAY_LATER', 'Pay Later'

    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='payments',
        db_column='booking_id'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_mode = models.CharField(max_length=32, choices=PaymentMode.choices, default=PaymentMode.PAY_NOW)
    status = models.CharField(max_length=32, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.amount} for {self.booking_id} ({self.status})"
