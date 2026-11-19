import logging
import re
import urllib.request
import urllib.error
import json
from typing import Any, Dict, Optional
from django.conf import settings

logger = logging.getLogger("whatsapp.utils.client")


def normalize_phone_number(phone: str) -> str:
    """
    Normalizes a phone number for WhatsApp Cloud API.
    - Strips spaces, dashes, parentheses, plus signs.
    - If 10 digits (standard Indian mobile without country code), prepends 91.
    """
    if not phone:
        return ""
    digits = re.sub(r"\D", "", str(phone))
    if len(digits) == 10:
        return f"91{digits}"
    return digits


def send_whatsapp_http_request(
    to_phone: str,
    message_text: str,
    template_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Sends a message via the Meta WhatsApp Cloud API.
    If API token or Phone Number ID are not yet configured in .env,
    gracefully logs and returns a prepared/dry-run response without crashing.
    """
    normalized = normalize_phone_number(to_phone)
    if not normalized:
        return {"success": False, "status": "failed", "error": "Invalid or missing phone number"}

    api_token = getattr(settings, "WHATSAPP_API_TOKEN", "")
    phone_number_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "")

    # Dry-run / prepared mode when credentials are not yet configured
    if not api_token or not phone_number_id:
        logger.info(
            "[WhatsApp Dry-Run] Message prepared for %s [Template: %s]:\n%s",
            normalized,
            template_name or "text",
            message_text,
        )
        return {
            "success": True,
            "status": "prepared",
            "message_id": f"dry_run_{normalized}_{abs(hash(message_text)) % 1000000}",
            "phone": normalized,
            "template": template_name,
            "mode": "dry_run",
            "note": "Configure WHATSAPP_API_TOKEN and WHATSAPP_PHONE_NUMBER_ID in .env to dispatch live WhatsApp messages.",
        }

    # Live Meta WhatsApp Cloud API call
    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": normalized,
        "type": "text",
        "text": {"preview_url": True, "body": message_text},
    }

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp_body = resp.read().decode("utf-8")
            data = json.loads(resp_body)
            msg_id = (data.get("messages") or [{}])[0].get("id", "")
            logger.info("WhatsApp message sent successfully to %s: ID=%s", normalized, msg_id)
            return {
                "success": True,
                "status": "sent",
                "message_id": msg_id,
                "provider_response": data,
            }
    except urllib.error.HTTPError as http_err:
        err_content = http_err.read().decode("utf-8", errors="replace")
        logger.error("WhatsApp API HTTP error (%s): %s", http_err.code, err_content)
        return {
            "success": False,
            "status": "failed",
            "error": f"HTTP {http_err.code}",
            "details": err_content,
        }
    except Exception as exc:
        logger.exception("WhatsApp API network error: %s", exc)
        return {
            "success": False,
            "status": "failed",
            "error": str(exc),
        }
