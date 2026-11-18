import json
import logging
from typing import Any, Dict, Union
from .models import Lead

logger = logging.getLogger(__name__)


def lead_from_funnel(payload: Union[Dict[str, Any], str]) -> Lead:
    """
    Core handler function to parse, sanitize, and persist incoming webhook data from funnels into the Lead model.
    Handles nested structures (like ronak_electronics_funnel) as well as flat contact payloads.
    """
    if isinstance(payload, str):
        try:
            payload_dict = json.loads(payload)
        except json.JSONDecodeError as err:
            logger.error("Failed to decode JSON payload string in lead_from_funnel: %s", err)
            payload_dict = {"raw_text": payload}
    elif isinstance(payload, dict):
        payload_dict = payload
    else:
        payload_dict = {"raw_data": str(payload)}

    # Top-level event & source metadata
    event_type = payload_dict.get("event") or payload_dict.get("event_type") or "tv_repair_inquiry"
    source = payload_dict.get("source") or "ronak_electronics_funnel"

    # Dig into nested 'data' if present
    data = payload_dict.get("data")
    if isinstance(data, dict):
        context = data
    else:
        context = payload_dict

    customer = context.get("customer") if isinstance(context.get("customer"), dict) else {}

    # 1. Extract Name
    name = (
        customer.get("name")
        or context.get("name")
        or context.get("customerName")
        or context.get("full_name")
        or context.get("fullName")
        or "Website Inquirer"
    ).strip()

    # 2. Extract Phone
    phone = str(
        customer.get("phone")
        or context.get("phone")
        or context.get("mobile")
        or context.get("mobileNumber")
        or context.get("phoneNumber")
        or ""
    ).strip()

    # 3. Extract Email
    email = customer.get("email") or context.get("email") or None
    if email:
        email = str(email).strip().lower()

    # 4. Extract Problem / Message Description
    problem_description = (
        customer.get("problem")
        or context.get("problem")
        or context.get("message")
        or context.get("issue")
        or context.get("description")
        or ""
    ).strip()

    # 5. Extract Booking Reference ID
    booking_id = (
        context.get("bookingId")
        or context.get("booking_id")
        or payload_dict.get("bookingId")
        or payload_dict.get("booking_id")
        or ""
    ).strip()

    # 6. Extract Service Name
    service_obj = context.get("service")
    if isinstance(service_obj, dict):
        service_type = service_obj.get("name") or service_obj.get("id") or ""
    else:
        service_type = str(context.get("service") or context.get("service_type") or "").strip()

    # 7. Extract Service Center / Lab
    metadata_obj = context.get("metadata")
    if isinstance(metadata_obj, dict):
        service_center = metadata_obj.get("assignedCenter") or "Ronak Electronics Service Center, Surat"
    else:
        service_center = context.get("service_center") or "Ronak Electronics Service Center, Surat"

    # 8. Extract Payment Info
    payment_obj = context.get("payment")
    if isinstance(payment_obj, dict):
        is_paid = bool(payment_obj.get("isPaid", False))
        try:
            amount = float(payment_obj.get("amount", 0.0) or 0.0)
        except (ValueError, TypeError):
            amount = 0.00
    else:
        is_paid = bool(context.get("is_paid", False))
        try:
            amount = float(context.get("amount", 0.0) or 0.0)
        except (ValueError, TypeError):
            amount = 0.00

    # Create and persist the Lead instance
    lead = Lead.objects.create(
        name=name,
        phone=phone,
        email=email,
        problem_description=problem_description,
        service_type=service_type,
        service_center=service_center,
        source=source,
        event_type=event_type,
        booking_id=booking_id,
        is_paid=is_paid,
        amount=amount,
        raw_payload=payload_dict,
        status="new",
    )

    logger.info("Successfully created Lead #%s (%s, %s) from funnel event '%s'", lead.id, lead.name, lead.phone, event_type)
    return lead
