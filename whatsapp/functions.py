import logging
import re
from typing import Any, Dict, List, Optional
from django.utils import timezone
from .models import WhatsAppMessageLog
from .utils.client import normalize_phone_number, send_whatsapp_http_request
from .utils.defaults import DEFAULT_TEMPLATES

logger = logging.getLogger("whatsapp.functions")

# Pure Python Template Definitions (No Database Model Schema)
MESSAGE_TEMPLATES = DEFAULT_TEMPLATES


def safe_format(template_str: str, context: Dict[str, Any]) -> str:
    """
    Safely formats a string template containing {placeholders} without raising KeyError.
    Missing placeholders are replaced with empty string or sensible fallback.
    """
    def replace_match(match):
        key = match.group(1)
        val = context.get(key)
        if val is None:
            return ""
        return str(val)

    return re.sub(r"\{([a-zA-Z0-9_]+)\}", replace_match, template_str)


def render_template(template_type: str, context: Dict[str, Any]) -> str:
    """
    Pure Python template renderer.
    Fetches template text directly from MESSAGE_TEMPLATES dictionary.
    No database queries or model schemas needed.
    """
    # 1. Check template definition in pure Python dictionary
    tpl_def = MESSAGE_TEMPLATES.get(template_type)
    if tpl_def and "body" in tpl_def:
        return safe_format(tpl_def["body"], context)

    # 2. Fallback for custom message body
    if "message_body" in context:
        return str(context["message_body"])

    return f"Notification from Ronak Electronics: {template_type}"


def send_whatsapp_message(
    phone: str,
    template_type: str,
    context: Optional[Dict[str, Any]] = None,
    lead: Any = None,
    booking_id: str = "",
) -> WhatsAppMessageLog:
    """
    Base function: renders template, invokes WhatsApp Cloud API, and logs result in WhatsAppMessageLog.
    """
    ctx = dict(context or {})
    recipient_name = ctx.get("name") or getattr(lead, "name", "") or "Customer"
    resolved_booking_id = booking_id or ctx.get("booking_id") or getattr(lead, "booking_id", "") or ""

    # Ensure essential context keys exist
    ctx.setdefault("name", recipient_name)
    ctx.setdefault("booking_id", resolved_booking_id)

    # Render message body
    message_body = render_template(template_type, ctx)
    normalized_phone = normalize_phone_number(phone)

    # Dispatch via API client
    api_result = send_whatsapp_http_request(
        to_phone=normalized_phone,
        message_text=message_body,
        template_name=template_type,
    )

    status = "sent" if api_result.get("status") == "sent" else api_result.get("status", "prepared")
    message_id = api_result.get("message_id", "")
    error_msg = api_result.get("error", "")

    # Save to WhatsAppMessageLog
    log_entry = WhatsAppMessageLog.objects.create(
        phone=normalized_phone or phone,
        recipient_name=recipient_name,
        template_type=template_type,
        message_body=message_body,
        status=status,
        lead=lead if hasattr(lead, "id") else None,
        booking_id=resolved_booking_id,
        whatsapp_message_id=message_id,
        payload=ctx,
        provider_response=api_result,
        error_message=error_msg,
    )

    logger.info(
        "WhatsApp message created: LogID=%s Type=%s Phone=%s Status=%s",
        log_entry.id,
        template_type,
        log_entry.phone,
        status,
    )
    return log_entry


# -----------------------------------------------------------------------------
# Specific Template Trigger Functions (Trigger based on your wish)
# -----------------------------------------------------------------------------

def send_lead_welcome_message(
    phone: str,
    name: str = "Customer",
    problem: str = "TV Repair Consultation",
    lead: Any = None,
) -> WhatsAppMessageLog:
    """
    Trigger 1: New Lead / Visitor Inquiry Welcome
    Sends warm acknowledgement to customer who submitted initial inquiry or web visit.
    """
    context = {
        "name": name,
        "problem": problem or "Television Service & Diagnostics",
    }
    return send_whatsapp_message(
        phone=phone,
        template_type="lead_welcome",
        context=context,
        lead=lead,
    )


def send_booking_confirmation_message(
    phone: str,
    name: str,
    booking_id: str,
    tv_brand: str = "Multi-Brand",
    date: str = "Tomorrow",
    time_slot: str = "Morning Slot",
    address: str = "Customer Doorstep Address",
    screen_size: str = "",
    lead: Any = None,
) -> WhatsAppMessageLog:
    """
    Trigger 2: Doorstep TV Repair Booking Confirmation
    Sends appointment details, booking ID, date, time slot, and address.
    """
    context = {
        "name": name,
        "booking_id": booking_id,
        "tv_brand": tv_brand,
        "screen_size": f"({screen_size})" if screen_size else "",
        "date": date,
        "time_slot": time_slot,
        "address": address,
    }
    return send_whatsapp_message(
        phone=phone,
        template_type="booking_confirmation",
        context=context,
        lead=lead,
        booking_id=booking_id,
    )


def send_visiting_fee_paid_message(
    phone: str,
    name: str,
    booking_id: str,
    amount: Any,
    payment_id: str = "",
    date: str = "",
    time_slot: str = "",
    lead: Any = None,
) -> WhatsAppMessageLog:
    """
    Trigger 3: Advance Visiting Fee Payment Receipt
    Triggered when Razorpay visiting deposit is paid.
    """
    context = {
        "name": name,
        "booking_id": booking_id,
        "amount": amount,
        "payment_id": payment_id or "Direct Online Payment",
        "date": date or "Scheduled Date",
        "time_slot": time_slot or "Priority Slot",
    }
    return send_whatsapp_message(
        phone=phone,
        template_type="visiting_fee_paid",
        context=context,
        lead=lead,
        booking_id=booking_id,
    )


def send_technician_dispatched_message(
    phone: str,
    name: str,
    booking_id: str,
    technician_name: str = "Senior Engineer",
    technician_phone: str = "+91 98986 47777",
    eta: str = "30-45 Minutes",
    lead: Any = None,
) -> WhatsAppMessageLog:
    """
    Trigger 4: Technician On The Way
    Alerts the customer that the technician has departed for their doorstep.
    """
    context = {
        "name": name,
        "booking_id": booking_id,
        "technician_name": technician_name,
        "technician_phone": technician_phone,
        "eta": eta,
    }
    return send_whatsapp_message(
        phone=phone,
        template_type="technician_dispatched",
        context=context,
        lead=lead,
        booking_id=booking_id,
    )


def send_repair_status_update_message(
    phone: str,
    name: str,
    booking_id: str,
    tv_brand: str = "Television",
    status_text: str = "Under Inspection",
    notes: str = "Diagnostics in progress",
    estimated_delivery: str = "Within 24 Hours",
    lead: Any = None,
) -> WhatsAppMessageLog:
    """
    Trigger 5: Repair Status Update
    Keeps customer informed during bench repair, parts replacement, or screen testing.
    """
    context = {
        "name": name,
        "booking_id": booking_id,
        "tv_brand": tv_brand,
        "status_text": status_text,
        "notes": notes,
        "estimated_delivery": estimated_delivery,
    }
    return send_whatsapp_message(
        phone=phone,
        template_type="repair_status_update",
        context=context,
        lead=lead,
        booking_id=booking_id,
    )


def send_repair_completed_message(
    phone: str,
    name: str,
    booking_id: str,
    tv_brand: str = "Television",
    amount: Any = 0,
    warranty_period: str = "90 Days Service Warranty",
    lead: Any = None,
) -> WhatsAppMessageLog:
    """
    Trigger 6: Repair Completed & Tested
    Notifies customer that TV is repaired, passed test run, and ready for delivery.
    """
    context = {
        "name": name,
        "booking_id": booking_id,
        "tv_brand": tv_brand,
        "amount": amount,
        "warranty_period": warranty_period,
    }
    return send_whatsapp_message(
        phone=phone,
        template_type="repair_completed",
        context=context,
        lead=lead,
        booking_id=booking_id,
    )


def send_call_click_acknowledgement_message(
    phone: str,
    name: str = "Customer",
    lead: Any = None,
) -> WhatsAppMessageLog:
    """
    Trigger 7: Call Click Acknowledgement
    Sent when visitor clicked Call on website or requested immediate callback.
    """
    context = {"name": name}
    return send_whatsapp_message(
        phone=phone,
        template_type="call_click_acknowledgement",
        context=context,
        lead=lead,
    )


def send_lead_followup_message(
    phone: str,
    name: str = "Customer",
    lead: Any = None,
) -> WhatsAppMessageLog:
    """
    Trigger 8: Marketing & Inquiry Follow-Up
    Re-engages inactive inquiries with offer of same-day doorstep visit.
    """
    context = {"name": name}
    return send_whatsapp_message(
        phone=phone,
        template_type="lead_followup",
        context=context,
        lead=lead,
    )


def send_custom_whatsapp_message(
    phone: str,
    message_body: str,
    name: str = "Customer",
    lead: Any = None,
    booking_id: str = "",
) -> WhatsAppMessageLog:
    """
    Trigger 9: Custom Direct Message
    Allows sending any arbitrary message text whenever you wish.
    """
    context = {
        "name": name,
        "message_body": message_body,
        "booking_id": booking_id,
    }
    return send_whatsapp_message(
        phone=phone,
        template_type="custom",
        context=context,
        lead=lead,
        booking_id=booking_id,
    )


def trigger_whatsapp_by_type(
    template_type: str,
    phone: str,
    context: Optional[Dict[str, Any]] = None,
    lead: Any = None,
) -> WhatsAppMessageLog:
    """
    Master Dispatcher:
    Triggers ANY message template dynamically based on string type name.
    Useful for webhooks, automation cron jobs, or frontend triggers.
    """
    ctx = dict(context or {})
    name = ctx.get("name") or "Customer"
    booking_id = ctx.get("booking_id") or ""

    if template_type == "lead_welcome":
        return send_lead_welcome_message(phone=phone, name=name, problem=ctx.get("problem", ""), lead=lead)
    elif template_type == "booking_confirmation":
        return send_booking_confirmation_message(
            phone=phone,
            name=name,
            booking_id=booking_id,
            tv_brand=ctx.get("tv_brand", "Multi-Brand"),
            date=ctx.get("date", ""),
            time_slot=ctx.get("time_slot", ""),
            address=ctx.get("address", ""),
            screen_size=ctx.get("screen_size", ""),
            lead=lead,
        )
    elif template_type == "visiting_fee_paid":
        return send_visiting_fee_paid_message(
            phone=phone,
            name=name,
            booking_id=booking_id,
            amount=ctx.get("amount", 0),
            payment_id=ctx.get("payment_id", ""),
            date=ctx.get("date", ""),
            time_slot=ctx.get("time_slot", ""),
            lead=lead,
        )
    elif template_type == "technician_dispatched":
        return send_technician_dispatched_message(
            phone=phone,
            name=name,
            booking_id=booking_id,
            technician_name=ctx.get("technician_name", "Senior Engineer"),
            technician_phone=ctx.get("technician_phone", "+91 98986 47777"),
            eta=ctx.get("eta", "30-45 Minutes"),
            lead=lead,
        )
    elif template_type == "repair_status_update":
        return send_repair_status_update_message(
            phone=phone,
            name=name,
            booking_id=booking_id,
            tv_brand=ctx.get("tv_brand", "Television"),
            status_text=ctx.get("status_text", "In Repair"),
            notes=ctx.get("notes", ""),
            estimated_delivery=ctx.get("estimated_delivery", ""),
            lead=lead,
        )
    elif template_type == "repair_completed":
        return send_repair_completed_message(
            phone=phone,
            name=name,
            booking_id=booking_id,
            tv_brand=ctx.get("tv_brand", "Television"),
            amount=ctx.get("amount", 0),
            warranty_period=ctx.get("warranty_period", "90 Days Service Warranty"),
            lead=lead,
        )
    elif template_type == "call_click_acknowledgement":
        return send_call_click_acknowledgement_message(phone=phone, name=name, lead=lead)
    elif template_type == "lead_followup":
        return send_lead_followup_message(phone=phone, name=name, lead=lead)
    elif template_type == "custom":
        return send_custom_whatsapp_message(
            phone=phone,
            message_body=ctx.get("message_body", ""),
            name=name,
            lead=lead,
            booking_id=booking_id,
        )
    else:
        # Generic template fallback
        return send_whatsapp_message(phone=phone, template_type=template_type, context=ctx, lead=lead, booking_id=booking_id)


def list_whatsapp_messages(
    template_type: Optional[str] = None,
    status: Optional[str] = None,
    phone: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Returns sanitized list of logged WhatsApp messages for admin dashboards.
    """
    qs = WhatsAppMessageLog.objects.all().order_by("-created_at")

    if template_type:
        qs = qs.filter(template_type=template_type)
    if status:
        qs = qs.filter(status=status)
    if phone:
        qs = qs.filter(phone__icontains=phone)

    logs = qs[offset : offset + limit]

    return [
        {
            "id": log.id,
            "phone": log.phone,
            "recipient_name": log.recipient_name,
            "template_type": log.template_type,
            "message_body": log.message_body,
            "status": log.status,
            "booking_id": log.booking_id,
            "lead_id": log.lead_id,
            "whatsapp_message_id": log.whatsapp_message_id,
            "error_message": log.error_message,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
