import json
import logging
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .services import lead_from_funnel
from .models import Lead

logger = logging.getLogger(__name__)


@csrf_exempt
def tv_repair_webhook(request: HttpRequest) -> HttpResponse:
    """
    Webhook endpoint dedicated for Ronak Electronics TV repair funnel.
    URL: /api/webhooks/tv-repair/
    Accepts arbitrary JSON payloads, extracts lead data, and saves to SQLite.
    """
    if request.method == "GET":
        return JsonResponse({
            "status": "online",
            "endpoint": "/api/webhooks/tv-repair/",
            "message": "Ronak Electronics Webhook receiver is ready to accept POST payloads.",
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
        lead = lead_from_funnel(payload)
        return JsonResponse({
            "success": True,
            "message": "Lead received and saved to database successfully",
            "lead": {
                "id": lead.id,
                "name": lead.name,
                "phone": lead.phone,
                "booking_id": lead.booking_id,
                "status": lead.status,
                "created_at": lead.created_at.isoformat(),
            }
        }, status=201)
    except Exception as exc:
        logger.exception("Error processing funnel lead webhook: %s", exc)
        return JsonResponse({
            "success": False,
            "error": "Failed to process lead",
            "details": str(exc),
        }, status=500)


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
        lead = lead_from_funnel(payload)
        return JsonResponse({
            "success": True,
            "message": "Lead captured successfully",
            "lead_id": lead.id,
            "booking_id": lead.booking_id,
        }, status=201)
    except Exception as exc:
        logger.exception("Error processing generic lead webhook: %s", exc)
        return JsonResponse({"success": False, "error": str(exc)}, status=500)


def lead_list_api(request: HttpRequest) -> HttpResponse:
    """
    Simple JSON view to list the latest 50 captured leads.
    URL: /api/leads/
    """
    leads = Lead.objects.all().order_by("-created_at")[:50]
    data = [
        {
            "id": l.id,
            "name": l.name,
            "phone": l.phone,
            "problem": l.problem_description,
            "service": l.service_type,
            "service_center": l.service_center,
            "booking_id": l.booking_id,
            "status": l.status,
            "is_paid": l.is_paid,
            "amount": float(l.amount),
            "created_at": l.created_at.isoformat(),
        }
        for l in leads
    ]
    return JsonResponse({"total": Lead.objects.count(), "leads": data})
