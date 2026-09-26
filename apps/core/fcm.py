import logging
import uuid
import os
from django.conf import settings

logger = logging.getLogger('yajaman.fcm')

_firebase_initialized = False

def get_firebase_app():
    global _firebase_initialized
    if _firebase_initialized:
        return True

    cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
    if cred_path and os.path.exists(cred_path):
        try:
            import firebase_admin
            from firebase_admin import credentials
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            _firebase_initialized = True
            logger.info("Firebase Admin SDK initialized with credentials at %s", cred_path)
            return True
        except Exception as e:
            logger.error("Failed to initialize Firebase Admin SDK: %s", e)
            return False
    return False


def send_fcm_message(token: str, title: str, body: str, data: dict = None) -> str:
    """
    Sends an FCM message to a specific device token.
    Uses Firebase Admin SDK if configured, otherwise logs message and returns a mock ID.
    """
    data = {str(k): str(v) for k, v in (data or {}).items()}

    if get_firebase_app():
        try:
            from firebase_admin import messaging
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data,
                token=token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        channel_id='booking_alerts',
                    ),
                ),
                apns=messaging.APNSConfig(
                    headers={'apns-priority': '10'},
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            content_available=True,
                        ),
                    ),
                ),
            )
            response = messaging.send(message)
            logger.info("FCM push sent successfully to token %s: %s", token[:10], response)
            return response
        except Exception as e:
            logger.error("FCM push error for token %s: %s", token[:10], e)
            return f"err-{uuid.uuid4()}"

    # Dev/Mock fallback
    simulated_msg_id = f"sim-fcm-{uuid.uuid4()}"
    logger.info(
        "[FCM MOCK PUSH] Sent to %s | Title: '%s' | Body: '%s' | Data: %s | ID: %s",
        token[:15] if token else "NO_TOKEN",
        title,
        body,
        data,
        simulated_msg_id
    )
    return simulated_msg_id


def send_vendor_dispatch_notification(vendor_device, booking, distance_km=0.0):
    """
    Sends 'NEW_BOOKING_REQUEST' push notification to an eligible vendor.
    Frontend React Native app receives this in background/killed/foreground.
    """
    if not vendor_device or not vendor_device.fcm_token:
        return None

    service_name = booking.service.name if booking.service else "Service Booking"
    customer_locality = (
        booking.snapshot_booking_address.get('street_area_locality') or
        booking.snapshot_booking_address.get('city') or
        "Customer Location"
    )

    title = f"New Booking Request: {service_name}"
    body = f"Locality: {customer_locality} ({distance_km:.1f} km away). Date: {booking.preferred_date} at {booking.preferred_time_slot}"
    
    data = {
        "event_type": "NEW_BOOKING_REQUEST",
        "booking_id": str(booking.id),
        "service_name": service_name,
        "pricing_variant": str(booking.pricing_variant),
        "total_price": str(booking.total_price),
        "preferred_date": str(booking.preferred_date),
        "preferred_time_slot": str(booking.preferred_time_slot),
        "distance_km": f"{distance_km:.1f}",
        "customer_name": booking.user.full_name if booking.user else "Customer",
        "customer_city": booking.snapshot_booking_address.get('city', ''),
        "customer_locality": customer_locality,
    }

    return send_fcm_message(
        token=vendor_device.fcm_token,
        title=title,
        body=body,
        data=data,
    )


def send_customer_assignment_notification(user_device, booking, vendor):
    """
    Sends 'VENDOR_ASSIGNED' push notification to the customer.
    """
    if not user_device or not user_device.fcm_token:
        return None

    service_name = booking.service.name if booking.service else "Your Booking"
    title = "Vendor Assigned to Your Booking!"
    body = f"{vendor.name} has accepted your {service_name} scheduled for {booking.preferred_date}."

    data = {
        "event_type": "VENDOR_ASSIGNED",
        "booking_id": str(booking.id),
        "service_name": service_name,
        "vendor_id": str(vendor.id),
        "vendor_name": vendor.name,
        "vendor_phone": vendor.phone_number,
        "vendor_rating": str(vendor.rating_average),
        "vendor_qualification": vendor.qualification or "",
        "vendor_origin_city": vendor.origin_city or "",
        "vendor_origin_state": vendor.origin_state or "",
    }

    return send_fcm_message(
        token=user_device.fcm_token,
        title=title,
        body=body,
        data=data,
    )
