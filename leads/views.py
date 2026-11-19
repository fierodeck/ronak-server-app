import json
import logging
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .functions import (
    get_campaign_analytics,
    get_loyal_users,
    list_contact_inquiries_data,
    list_leads_data,
    save_or_update_lead,
)
from .models import Lead

logger = logging.getLogger("leads.views")


@csrf_exempt
def tv_repair_webhook(request: HttpRequest) -> HttpResponse:
    """
    Primary endpoint for TV repair bookings and inquiries.
    URL: /api/webhooks/tv-repair/ and /api/leads/booking/
    Accepts arbitrary JSON payloads, handles returning customer loyalty, and saves to database.
    """
    if request.method == "GET":
        return JsonResponse({
            "status": "online",
            "endpoint": "/api/webhooks/tv-repair/",
            "message": "Ronak Electronics TV Repair Booking Receiver is online.",
            "total_leads_saved": Lead.objects.count(),
        })

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    try:
        if not request.body:
            return JsonResponse({"error": "Empty request body"}, status=400)

        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError as err:
        logger.error("Invalid JSON received: %s", err)
        return JsonResponse({"error": "Invalid JSON payload", "details": str(err)}, status=400)

    try:
        lead = save_or_update_lead(payload, source_override="ronak_electronics_web")
        contact_inq = lead.contact_inquiries.order_by("-created_at").first()
        return JsonResponse({
            "success": True,
            "message": "Lead received and saved to database successfully",
            "lead": {
                "id": lead.id,
                "name": lead.name,
                "phone": lead.phone,
                "email": lead.email,
                "booking_id": lead.booking_id,
                "visit_count": lead.visit_count,
                "status": lead.status,
                "created_at": lead.created_at.isoformat(),
            },
            "contact_inquiry_id": contact_inq.id if contact_inq else None,
        }, status=201)
    except Exception as exc:
        logger.exception("Error processing repair booking lead: %s", exc)
        return JsonResponse({
            "success": False,
            "error": "Failed to process lead",
            "details": str(exc),
        }, status=500)


@csrf_exempt
def page_visit_beacon(request: HttpRequest) -> HttpResponse:
    """
    Lightweight beacon endpoint to track visits, attribution, and returning users.
    URL: /api/leads/visit/
    Rule: 'for a person who has already visited uska counter ++ kro taki pta lage most loyal user'
    """
    if request.method != "POST":
        return JsonResponse({"status": "online", "message": "POST to record visitor beacon"}, status=200)

    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
        lead = save_or_update_lead(payload, source_override="web_visit", event_type_override="page_view")
        return JsonResponse({
            "success": True,
            "visit_count": lead.visit_count,
            "visitor_id": lead.visitor_id,
        }, status=200)
    except Exception as exc:
        logger.exception("Error processing visitor beacon: %s", exc)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


@csrf_exempt
def google_sync_lead(request: HttpRequest) -> HttpResponse:
    """
    Captures verified Google One Tap / Google Sign-in profile into the database.
    URL: /api/leads/google-sync/
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
        lead = save_or_update_lead(payload, source_override="google_one_tap", event_type_override="google_sign_in")
        return JsonResponse({
            "success": True,
            "lead_id": lead.id,
            "visit_count": lead.visit_count,
            "name": lead.name,
            "email": lead.email,
        }, status=201)
    except Exception as exc:
        logger.exception("Error syncing Google One Tap lead: %s", exc)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


@csrf_exempt
def generic_lead_webhook(request: HttpRequest) -> HttpResponse:
    """
    General lead webhook endpoint for any marketing funnel or contact form.
    URL: /api/webhooks/lead/
    """
    if request.method == "GET":
        return JsonResponse({
            "status": "online",
            "endpoint": "/api/webhooks/lead/",
            "message": "Generic Lead Webhook receiver is ready.",
        })

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
        lead = save_or_update_lead(payload)
        return JsonResponse({
            "success": True,
            "message": "Lead captured successfully",
            "lead_id": lead.id,
            "visit_count": lead.visit_count,
            "booking_id": lead.booking_id,
        }, status=201)
    except Exception as exc:
        logger.exception("Error processing generic lead webhook: %s", exc)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


def loyal_users_api(request: HttpRequest) -> HttpResponse:
    """
    JSON API returning loyal returning visitors (visit_count >= min_visits).
    URL: /api/leads/loyal-users/
    """
    min_visits = int(request.GET.get("min_visits", 2))
    limit = int(request.GET.get("limit", 50))
    users = get_loyal_users(min_visits=min_visits, limit=limit)
    return JsonResponse({
        "total_loyal_users": len(users),
        "min_visits_threshold": min_visits,
        "users": users,
    })


def campaign_analytics_api(request: HttpRequest) -> HttpResponse:
    """
    JSON API returning marketing campaign and ad channel breakdown.
    URL: /api/leads/campaigns/
    """
    stats = get_campaign_analytics()
    return JsonResponse(stats)


def lead_list_api(request: HttpRequest) -> HttpResponse:
    """
    JSON API to list recent leads with status and search filtering.
    URL: /api/leads/
    """
    status = request.GET.get("status")
    search = request.GET.get("search")
    limit = int(request.GET.get("limit", 50))
    offset = int(request.GET.get("offset", 0))

    leads = list_leads_data(status=status, search=search, limit=limit, offset=offset)
    return JsonResponse({
        "count": len(leads),
        "leads": leads,
    })


def contact_inquiries_api(request: HttpRequest) -> HttpResponse:
    """
    JSON API to list dedicated contact form inquiries.
    URL: /api/contact-inquiries/
    """
    status = request.GET.get("status")
    search = request.GET.get("search")
    limit = int(request.GET.get("limit", 50))
    offset = int(request.GET.get("offset", 0))

    inquiries = list_contact_inquiries_data(status=status, search=search, limit=limit, offset=offset)
    return JsonResponse({
        "count": len(inquiries),
        "inquiries": inquiries,
    })



@csrf_exempt
def register_fcm_token_api(request: HttpRequest) -> HttpResponse:
    """
    Registers an FCM device token for technicians or admins to receive instant push alerts.
    URL: /api/notifications/register-token/
    Payload: { "token": "...", "device_name": "...", "role": "technician" }
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8")) if request.body else {}
        token = (body.get("token") or "").strip()
        device_name = (body.get("device_name") or "Technician Device").strip()
        role = (body.get("role") or "technician").strip()

        if not token:
            return JsonResponse({"error": "Missing 'token' in request body"}, status=400)

        from .models import FCMDeviceToken

        device, created = FCMDeviceToken.objects.update_or_create(
            token=token,
            defaults={
                "device_name": device_name,
                "role": role,
                "is_active": True,
            },
        )
        return JsonResponse({
            "success": True,
            "created": created,
            "device": {
                "token": device.token[:12] + "...",
                "device_name": device.device_name,
                "role": device.role,
                "is_active": device.is_active,
            },
        }, status=201 if created else 200)
    except Exception as exc:
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


@csrf_exempt
def lead_event_api(request: HttpRequest) -> HttpResponse:
    """
    Captures high-intent customer click interactions as leads:
    - Phone Call Clicks (tel:...) -> source: 'phone_call', event_type: 'call_click'
    - WhatsApp Clicks (wa.me/...) -> source: 'whatsapp_click', event_type: 'whatsapp_click'
    - Custom Lead Actions
    
    Rule:
    'frontend pr visit bhi eak lead he and contact form is also lead call is alsso lead wp click is also lead'
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
        source = payload.get("source") or "phone_call"
        event_type = payload.get("event_type") or payload.get("event") or "interaction_click"

        lead = save_or_update_lead(
            payload,
            source_override=source,
            event_type_override=event_type,
        )
        return JsonResponse({
            "success": True,
            "lead_id": lead.id,
            "source": lead.source,
            "event_type": lead.event_type,
            "visit_count": lead.visit_count,
            "visitor_id": lead.visitor_id,
        }, status=200)
    except Exception as exc:
        logger.exception("Error processing lead event: %s", exc)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)

