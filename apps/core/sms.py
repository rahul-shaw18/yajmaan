import logging
import re
import requests
from django.conf import settings

logger = logging.getLogger('yajaman.sms')

FAST2SMS_BULK_V2_URL = "https://www.fast2sms.com/dev/bulkV2"


def clean_indian_phone_number(phone: str) -> str:
    """
    Extracts the clean 10-digit Indian mobile number required by Fast2SMS.
    Handles:
    - '+919876543210' -> '9876543210'
    - '919876543210'  -> '9876543210'
    - '09876543210'   -> '9876543210'
    - '98765 43210'   -> '9876543210'
    """
    digits = re.sub(r'\D', '', str(phone or ''))
    if len(digits) > 10:
        if digits.startswith('91') and len(digits) == 12:
            return digits[2:]
        if digits.startswith('0') and len(digits) == 11:
            return digits[1:]
        return digits[-10:]
    return digits


def send_fast2sms_otp(phone_number: str, otp_code: str) -> dict:
    """
    Sends an OTP via Fast2SMS using the 'otp' route of bulkV2 API.
    Fast2SMS sends: 'Your OTP: {#var#}'
    """
    api_key = getattr(settings, 'FAST2SMS_API_KEY', None)
    clean_phone = clean_indian_phone_number(phone_number)

    if len(clean_phone) != 10:
        logger.error("Invalid 10-digit Indian phone number: %s (cleaned: %s)", phone_number, clean_phone)
        return {
            "success": False,
            "message": f"Invalid mobile number '{phone_number}'. Must be a valid 10-digit Indian mobile number."
        }

    # If Fast2SMS API Key is NOT configured, log to console (Development / Mock mode)
    if not api_key:
        logger.warning(
            "[FAST2SMS MOCK] FAST2SMS_API_KEY not configured. Simulated OTP for %s: %s",
            clean_phone,
            otp_code
        )
        return {
            "success": True,
            "simulated": True,
            "message": "SMS simulated in dev mode (FAST2SMS_API_KEY not configured).",
            "otp": otp_code
        }

    # Send actual SMS via Fast2SMS API
    try:
        payload = {
            "authorization": api_key.strip(),
            "variables_values": str(otp_code),
            "route": "otp",
            "numbers": clean_phone,
        }
        headers = {
            "cache-control": "no-cache"
        }
        response = requests.get(
            FAST2SMS_BULK_V2_URL,
            params=payload,
            headers=headers,
            timeout=10
        )
        data = response.json()
        logger.info("Fast2SMS API response for %s: %s", clean_phone, data)

        if response.status_code == 200 and data.get("return") is True:
            msg_list = data.get("message", ["SMS sent successfully."])
            return {
                "success": True,
                "simulated": False,
                "request_id": data.get("request_id"),
                "message": msg_list[0] if isinstance(msg_list, list) else str(msg_list)
            }
        else:
            error_msg = data.get("message", "Failed to send SMS via Fast2SMS")
            if isinstance(error_msg, list):
                error_msg = error_msg[0]
            logger.error("Fast2SMS API returned failure for %s: %s", clean_phone, error_msg)
            return {
                "success": False,
                "message": str(error_msg)
            }
    except requests.exceptions.RequestException as e:
        logger.error("Fast2SMS API network error: %s", e)
        return {
            "success": False,
            "message": f"Network error contacting Fast2SMS: {str(e)}"
        }
