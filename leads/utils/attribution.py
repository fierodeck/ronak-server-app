from typing import Any, Dict


def clean_string(val: Any) -> str:
    """Helper to safely clean string values without throwing errors."""
    if val is None:
        return ""
    return str(val).strip()


def extract_attribution_from_dict(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts multi-touch marketing attribution fields from arbitrary payloads.
    Handles top-level fields, raw_payload, or nested 'data'/'metadata' dictionaries.
    """
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    raw = payload.get("raw_payload") if isinstance(payload.get("raw_payload"), dict) else {}
    meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}

    def get_attr(key: str) -> str:
        return (
            payload.get(key)
            or data.get(key)
            or raw.get(key)
            or meta.get(key)
            or ""
        )

    return {
        "visitor_id": clean_string(get_attr("visitor_id")) or None,
        "utm_source": clean_string(get_attr("utm_source")) or None,
        "utm_medium": clean_string(get_attr("utm_medium")) or None,
        "utm_campaign": clean_string(get_attr("utm_campaign")) or None,
        "utm_term": clean_string(get_attr("utm_term")) or None,
        "utm_content": clean_string(get_attr("utm_content")) or None,
        "gclid": clean_string(get_attr("gclid")) or None,
        "gad_source": clean_string(get_attr("gad_source")) or None,
        "gad_campaignid": clean_string(get_attr("gad_campaignid")) or None,
        "gbraid": clean_string(get_attr("gbraid")) or None,
        "wbraid": clean_string(get_attr("wbraid")) or None,
        "fbclid": clean_string(get_attr("fbclid")) or None,
        "landing_page": clean_string(get_attr("landing_page") or get_attr("path")) or None,
        "referrer": clean_string(get_attr("referrer")) or None,
    }


def extract_customer_from_dict(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts customer identity and repair problem details from arbitrary payloads.
    Supports both flat fields (name, phone, problem) and structured funnel payloads (customer, service, payment).
    """
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    context = data if data else payload
    customer = context.get("customer") if isinstance(context.get("customer"), dict) else {}
    service = context.get("service") if isinstance(context.get("service"), dict) else {}
    payment = context.get("payment") if isinstance(context.get("payment"), dict) else {}

    # Extract Name
    name = (
        customer.get("name")
        or context.get("name")
        or context.get("customerName")
        or context.get("fullName")
        or "Website Inquirer"
    )

    # Extract Phone
    phone = (
        customer.get("phone")
        or context.get("phone")
        or context.get("mobile")
        or context.get("mobileNumber")
        or ""
    )

    # Extract Email
    email = customer.get("email") or context.get("email") or None

    # Extract Problem / Description
    problem = (
        customer.get("problem")
        or service.get("issue")
        or service.get("issueDetails")
        or context.get("problem")
        or context.get("issue")
        or context.get("description")
        or ""
    )

    # Extract Service Type / TV Brand
    service_type = (
        service.get("tvBrand")
        or service.get("name")
        or context.get("tvBrand")
        or context.get("tv_brand")
        or context.get("service_type")
        or context.get("service")
        or "Multi-Brand"
    )

    # Extract TV Brand & Screen Size
    tv_brand = (
        service.get("tvBrand")
        or context.get("tvBrand")
        or context.get("tv_brand")
        or service_type
    )

    screen_size = (
        service.get("screenSize")
        or context.get("screenSize")
        or context.get("screen_size")
        or ""
    )

    # Extract Address
    address = (
        customer.get("address")
        or context.get("address")
        or context.get("customerAddress")
        or ""
    )

    # Extract Preferred Schedule
    scheduled_date = (
        service.get("scheduledDate")
        or context.get("scheduledDate")
        or context.get("date")
        or ""
    )

    scheduled_slot = (
        service.get("scheduledSlot")
        or context.get("scheduledSlot")
        or context.get("timeSlot")
        or context.get("time_slot")
        or ""
    )

    # Extract Booking Reference ID
    booking_id = (
        context.get("bookingId")
        or context.get("booking_id")
        or payload.get("bookingId")
        or payload.get("booking_id")
        or ""
    )

    # Extract Payment Info
    is_paid = bool(payment.get("isPaid", context.get("is_paid", False)))
    amount = float(payment.get("amount", context.get("amount", context.get("paidAmount", 0.0))) or 0.0)
    order_id = payment.get("orderId") or context.get("razorpay_order_id") or context.get("order_id") or ""
    payment_id = payment.get("paymentId") or context.get("razorpay_payment_id") or context.get("payment_id") or ""

    return {
        "name": clean_string(name),
        "phone": clean_string(phone),
        "email": clean_string(email).lower() if email else None,
        "address": clean_string(address),
        "tv_brand": clean_string(tv_brand),
        "screen_size": clean_string(screen_size),
        "scheduled_date": clean_string(scheduled_date),
        "scheduled_slot": clean_string(scheduled_slot),
        "problem_description": clean_string(problem),
        "service_type": clean_string(service_type),
        "booking_id": clean_string(booking_id),
        "is_paid": is_paid,
        "amount": amount,
        "order_id": clean_string(order_id),
        "payment_id": clean_string(payment_id),
    }
