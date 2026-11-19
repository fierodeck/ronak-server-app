import os
import json
import logging
from typing import Any, Dict, List, Optional
from django.conf import settings

logger = logging.getLogger("leads.utils.firebase")

# Global flag to track Firebase Admin initialization
_firebase_initialized = False


def initialize_firebase() -> bool:
    """
    Initializes the Firebase Admin SDK.
    Checks for service account JSON path from FIREBASE_CREDENTIALS_PATH setting or env var.
    If credentials are not yet configured, returns False gracefully without crashing.
    """
    global _firebase_initialized
    if _firebase_initialized:
        return True

    try:
        import firebase_admin
        from firebase_admin import credentials

        # Check if already initialized by another thread/process
        if firebase_admin._apps:
            _firebase_initialized = True
            return True

        cred_path = getattr(
            settings,
            "FIREBASE_CREDENTIALS_PATH",
            os.getenv("FIREBASE_CREDENTIALS_PATH", ""),
        )

        # 1. Path to service account JSON file
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            _firebase_initialized = True
            logger.info("Firebase Admin SDK successfully initialized from: %s", cred_path)
            return True

        # 2. Raw JSON string in environment variable
        cred_json_str = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")
        if cred_json_str:
            try:
                cred_dict = json.loads(cred_json_str)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                _firebase_initialized = True
                logger.info("Firebase Admin SDK successfully initialized from environment JSON string.")
                return True
            except Exception as json_err:
                logger.warning("Failed to parse FIREBASE_SERVICE_ACCOUNT_JSON: %s", json_err)

        logger.info(
            "Firebase credentials not yet provided (set FIREBASE_CREDENTIALS_PATH in .env). "
            "FCM notifications are ready in prepared/dry-run mode."
        )
        return False
    except ImportError:
        logger.warning("firebase_admin package not installed.")
        return False
    except Exception as exc:
        logger.error("Error initializing Firebase Admin SDK: %s", exc)
        return False


def send_fcm_notification(
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None,
    token: Optional[str] = None,
    topic: Optional[str] = "ronak_repair_alerts",
) -> Dict[str, Any]:
    """
    Dispatches a push notification via Firebase Cloud Messaging.
    
    If 'token' is provided: sends directly to that individual device.
    If 'token' is None: broadcasts to all active registered FCMDeviceTokens and the topic.
    """
    is_ready = initialize_firebase()
    data_dict = {str(k): str(v) for k, v in (data or {}).items()}

    if not is_ready:
        logger.info(
            "[Firebase Dry-Run] Notification prepared: Title='%s', Body='%s', Data=%s, Topic='%s'",
            title,
            body,
            data_dict,
            topic,
        )
        return {
            "success": True,
            "status": "prepared",
            "message": "Firebase SDK is ready. Provide service account JSON in FIREBASE_CREDENTIALS_PATH to send live push notifications.",
            "title": title,
            "body": body,
            "data": data_dict,
        }

    try:
        from firebase_admin import messaging

        notification = messaging.Notification(title=title, body=body)

        # 1. Send to single device token
        if token:
            message = messaging.Message(
                notification=notification,
                data=data_dict,
                token=token,
            )
            response = messaging.send(message)
            logger.info("FCM push sent successfully to token: %s", response)
            return {"success": True, "message_id": response}

        # 2. Broadcast to all registered active device tokens
        from ..models import FCMDeviceToken

        active_tokens = list(
            FCMDeviceToken.objects.filter(is_active=True).values_list("token", flat=True)
        )

        sent_count = 0
        failed_count = 0

        if active_tokens:
            multicast_message = messaging.MulticastMessage(
                notification=notification,
                data=data_dict,
                tokens=active_tokens,
            )
            batch_response = messaging.send_each_for_multicast(multicast_message)
            sent_count = batch_response.success_count
            failed_count = batch_response.failure_count

            # Deactivate invalid / unregistered tokens automatically
            for idx, resp in enumerate(batch_response.responses):
                if not resp.success and resp.exception:
                    err_code = getattr(resp.exception, "code", "")
                    if "registration-token-not-registered" in str(err_code) or "invalid-argument" in str(err_code):
                        bad_token = active_tokens[idx]
                        FCMDeviceToken.objects.filter(token=bad_token).update(is_active=False)
                        logger.info("Deactivated expired FCM token: %s", bad_token)

        # 3. Also send to topic if configured
        topic_msg_id = None
        if topic:
            try:
                topic_message = messaging.Message(
                    notification=notification,
                    data=data_dict,
                    topic=topic,
                )
                topic_msg_id = messaging.send(topic_message)
            except Exception as topic_err:
                logger.warning("FCM topic dispatch warning: %s", topic_err)

        return {
            "success": True,
            "active_devices_sent": sent_count,
            "failed_devices": failed_count,
            "topic_message_id": topic_msg_id,
        }
    except Exception as exc:
        logger.exception("Failed to send FCM notification: %s", exc)
        return {"success": False, "error": str(exc)}


def notify_new_lead_fcm(lead: Any) -> Dict[str, Any]:
    """
    Convenience function triggered when a new TV repair lead, call click, WhatsApp click, or booking arrives.
    Alerts on-duty technicians and shop admins.
    """
    phone_display = getattr(lead, "phone", "") or "Direct Click"
    customer_name = getattr(lead, "name", "") or "Customer"
    problem = getattr(lead, "problem_description", "") or getattr(lead, "service_type", "") or "TV Repair Inquiry"
    booking_id = getattr(lead, "booking_id", "") or f"ID-{lead.id}"
    visits = getattr(lead, "visit_count", 1)
    source = getattr(lead, "source", "ronak_electronics_web")

    if source == "phone_call":
        title = f"📞 Call Clicked: {customer_name}"
    elif source == "whatsapp_click":
        title = f"💬 WhatsApp Clicked: {customer_name}"
    elif source == "google_one_tap":
        title = f"✨ Google Verified Lead: {customer_name}"
    elif getattr(lead, "is_paid", False):
        title = f"💳 Paid Priority Booking: {customer_name} (₹{getattr(lead, 'amount', 0)})"
    else:
        title = f"🔔 TV Repair Lead: {customer_name}"

    body = f"{phone_display} • {problem[:85]}"
    if visits > 1:
        body += f" (Visits: {visits})"

    data = {
        "lead_id": str(lead.id),
        "booking_id": booking_id,
        "customer_name": customer_name,
        "phone": phone_display,
        "source": source,
        "status": getattr(lead, "status", "new"),
        "event_type": "new_lead_alert",
    }

    return send_fcm_notification(title=title, body=body, data=data, topic="ronak_repair_alerts")
