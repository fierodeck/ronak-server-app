import json
import logging
from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .functions import *
from .models import *
from .utils.defaults import DEFAULT_TEMPLATES

logger = logging.getLogger("whatsapp.views")


@csrf_exempt
def trigger_message_api(request: HttpRequest) -> HttpResponse:
    """
    HTTP API to trigger any WhatsApp message by template type.
    URL: /api/whatsapp/send/
    Method: POST
    Payload:
    {
        "type": "booking_confirmation",  // or "lead_welcome", "technician_dispatched", "repair_completed", etc.
        "phone": "+91 98986 47777",
        "name": "Customer Name",
        "booking_id": "RNK-TV-12345",
        "tv_brand": "Sony Bravia",
        ...
    }
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8")) if request.body else {}
    except json.JSONDecodeError as err:
        return JsonResponse({"error": "Invalid JSON body", "details": str(err)}, status=400)

    phone = (body.get("phone") or "").strip()
    template_type = (body.get("type") or body.get("template_type") or "custom").strip()

    if not phone:
        return JsonResponse({"error": "Missing required field: 'phone'"}, status=400)

    try:
        # Check if linked to an existing lead ID
        lead_id = body.get("lead_id")
        lead = None
        if lead_id:
            from leads.models import Lead
            lead = Lead.objects.filter(id=lead_id).first()

        log_entry = trigger_whatsapp_by_type(
            template_type=template_type,
            phone=phone,
            context=body,
            lead=lead,
        )

        return JsonResponse({
            "success": True,
            "message": "WhatsApp message triggered successfully",
            "log": {
                "id": log_entry.id,
                "phone": log_entry.phone,
                "template_type": log_entry.template_type,
                "status": log_entry.status,
                "booking_id": log_entry.booking_id,
                "message_body": log_entry.message_body,
                "created_at": log_entry.created_at.isoformat(),
            },
        }, status=201)
    except Exception as exc:
        logger.exception("Error triggering WhatsApp message: %s", exc)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


def list_messages_api(request: HttpRequest) -> HttpResponse:
    """
    JSON API returning audit log of all sent/prepared WhatsApp messages.
    URL: /api/whatsapp/logs/
    """
    template_type = request.GET.get("type")
    status = request.GET.get("status")
    phone = request.GET.get("phone")
    limit = int(request.GET.get("limit", 50))
    offset = int(request.GET.get("offset", 0))

    logs = list_whatsapp_messages(
        template_type=template_type,
        status=status,
        phone=phone,
        limit=limit,
        offset=offset,
    )
    return JsonResponse({
        "count": len(logs),
        "messages": logs,
    })


def list_templates_api(request: HttpRequest) -> HttpResponse:
    """
    JSON API returning all available WhatsApp message templates defined in Python.
    URL: /api/whatsapp/templates/
    """
    return JsonResponse({
        "total_templates": len(DEFAULT_TEMPLATES),
        "templates": [
            {
                "type": k,
                "title": v.get("title", k),
                "category": v.get("category", "transactional"),
                "description": v.get("description", ""),
                "sample_body": v.get("body", ""),
            }
            for k, v in DEFAULT_TEMPLATES.items()
        ],
    })


@csrf_exempt
def whatsapp_webhook_api(request: HttpRequest) -> HttpResponse:
    """
    Webhook endpoint for Meta WhatsApp Cloud API.
    GET: Handles Webhook Verification Challenge.
    POST: Receives real-time delivery status updates (sent, delivered, read) & inbound replies.
    URL: /api/whatsapp/webhook/
    """
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        expected_token = getattr(settings, "WHATSAPP_WEBHOOK_VERIFY_TOKEN", "ronak_whatsapp_verify_token")

        if mode == "subscribe" and token == expected_token:
            logger.info("WhatsApp webhook verified successfully!")
            return HttpResponse(challenge, content_type="text/plain", status=200)
        return HttpResponse("Verification token mismatch", status=403)

    if request.method == "POST":
        try:
            body = json.loads(request.body.decode("utf-8")) if request.body else {}
            # Update delivery status if status notification
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    statuses = value.get("statuses", [])
                    for s in statuses:
                        msg_id = s.get("id")
                        new_status = s.get("status")  # sent, delivered, read, failed
                        if msg_id and new_status:
                            WhatsAppMessageLog.objects.filter(whatsapp_message_id=msg_id).update(status=new_status)
                            logger.info("Updated status for WhatsApp msg %s -> %s", msg_id, new_status)

            return JsonResponse({"status": "received"}, status=200)
        except Exception as exc:
            logger.exception("Error processing WhatsApp webhook: %s", exc)
            return JsonResponse({"status": "error", "error": str(exc)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)
