import logging
from django.db import transaction
from django.db.models import Q
from apps.core.utils import calculate_haversine_distance
from apps.core.fcm import (
    send_vendor_dispatch_notification,
    send_customer_assignment_notification
)
from apps.vendors.models import Vendor, VendorDevice
from apps.accounts.models import UserDevice
from .models import Booking, BookingDispatchLog

logger = logging.getLogger('yajaman.dispatch')


class BookingDispatchError(Exception):
    pass


class BookingAlreadyAcceptedError(BookingDispatchError):
    pass


class BookingInvalidStateError(BookingDispatchError):
    pass


def find_eligible_vendors(booking: Booking):
    """
    Finds and ranks all eligible vendors for a booking:
    1. Category / skill matching (Generic: Barber vs Massage vs Pandit)
    2. Active and available status
    3. Within custom service radius (Haversine distance)
    4. Prioritized by origin state/city match, distance, and rating
    """
    category = booking.service.category
    cat_ids = [category.id]
    if category.parent_id:
        cat_ids.append(category.parent_id)

    # Filter vendors matching category (or vendors without restrictive category tags)
    candidates = Vendor.objects.filter(
        is_active=True,
        is_available=True
    ).filter(
        Q(categories__isnull=True) | Q(categories__id__in=cat_ids)
    ).distinct()

    # Customer location from address snapshot or relation
    cust_lat = booking.address.latitude
    cust_lon = booking.address.longitude

    # Customer spiritual origin
    origin_info = booking.snapshot_user_spiritual_origin or {}
    user_state = (origin_info.get('origin_state') or '').strip().lower()
    user_city = (origin_info.get('origin_city') or '').strip().lower()

    ranked_vendors = []

    for vendor in candidates:
        if vendor.current_latitude is None or vendor.current_longitude is None:
            # Skip vendors with no coordinates set
            continue

        distance = calculate_haversine_distance(
            float(cust_lat), float(cust_lon),
            float(vendor.current_latitude), float(vendor.current_longitude)
        )

        radius = float(vendor.service_radius_km or 15.0)
        if distance > radius:
            continue

        # Priority calculation
        priority_score = 0
        vendor_state = (vendor.origin_state or '').strip().lower()
        vendor_city = (vendor.origin_city or '').strip().lower()

        if user_state and vendor_state == user_state:
            priority_score += 50
            if user_city and vendor_city == user_city:
                priority_score += 50

        ranked_vendors.append({
            'vendor': vendor,
            'distance_km': round(distance, 2),
            'priority_score': priority_score,
            'rating': float(vendor.rating_average or 0.0),
        })

    # Sort: highest priority score first, then shortest distance, then highest rating
    ranked_vendors.sort(key=lambda x: (-x['priority_score'], x['distance_km'], -x['rating']))
    return ranked_vendors


def dispatch_booking_to_vendors(booking: Booking) -> int:
    """
    Dispatches booking to all eligible vendors via Firebase Cloud Messaging push notifications.
    Creates BookingDispatchLog entries for each vendor.
    """
    booking.status = Booking.BookingStatus.SEARCHING_VENDOR
    booking.save(update_fields=['status', 'updated_at'])

    eligible = find_eligible_vendors(booking)
    dispatched_count = 0

    for item in eligible:
        vendor = item['vendor']
        distance_km = item['distance_km']

        # Get vendor devices
        devices = VendorDevice.objects.filter(vendor=vendor)
        last_msg_id = None

        if devices.exists():
            for device in devices:
                msg_id = send_vendor_dispatch_notification(device, booking, distance_km)
                if msg_id:
                    last_msg_id = msg_id
        else:
            # Fallback mock id if device token not yet registered
            last_msg_id = f"sim-dispatch-{vendor.id}"

        # Create or update dispatch log
        BookingDispatchLog.objects.update_or_create(
            booking=booking,
            vendor=vendor,
            defaults={
                'fcm_message_id': last_msg_id,
                'response_status': 'DISPATCHED'
            }
        )
        dispatched_count += 1

    logger.info("Booking %s dispatched to %d eligible vendors", booking.id, dispatched_count)
    return dispatched_count


def accept_booking(booking_id, vendor: Vendor) -> Booking:
    """
    First-accept handler with atomic database row lock (select_for_update).
    Protects against race conditions when multiple vendors accept at the same time.
    """
    with transaction.atomic():
        booking = Booking.objects.select_for_update().get(id=booking_id)

        if booking.vendor is not None or booking.status == Booking.BookingStatus.ACCEPTED:
            raise BookingAlreadyAcceptedError("This booking has already been accepted by another vendor.")

        if booking.status in (Booking.BookingStatus.CANCELLED, Booking.BookingStatus.COMPLETED):
            raise BookingInvalidStateError("This booking is no longer available.")

        # Assign vendor and update status
        booking.vendor = vendor
        booking.status = Booking.BookingStatus.ACCEPTED
        booking.save(update_fields=['vendor', 'status', 'updated_at'])

        # Update dispatch logs
        BookingDispatchLog.objects.filter(booking=booking, vendor=vendor).update(response_status='ACCEPTED')
        BookingDispatchLog.objects.filter(booking=booking).exclude(vendor=vendor).filter(response_status='DISPATCHED').update(response_status='EXPIRED')

        # Send push notification to customer
        user_device = UserDevice.objects.filter(user=booking.user).order_by('-updated_at').first()
        if user_device:
            send_customer_assignment_notification(user_device, booking, vendor)

        logger.info("Booking %s accepted by vendor %s (%s)", booking.id, vendor.name, vendor.id)
        return booking


def reject_booking(booking_id, vendor: Vendor):
    """
    Records a vendor's rejection of a dispatched booking.
    """
    BookingDispatchLog.objects.filter(booking_id=booking_id, vendor=vendor).update(response_status='REJECTED')
