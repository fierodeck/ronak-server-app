import json
import logging
from typing import Any, Dict, List, Optional, Union
from django.db.models import Count, Q, Sum
from django.utils import timezone
from .models import Lead, ContactInquiry
from .utils.attribution import extract_attribution_from_dict, extract_customer_from_dict
from .utils.firebase import notify_new_lead_fcm

logger = logging.getLogger("leads.functions")


def parse_payload(payload: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """Safely parse payload into a Python dictionary."""
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except json.JSONDecodeError as err:
            logger.error("Failed to parse JSON payload in functions: %s", err)
            return {"raw_text": payload}
    elif isinstance(payload, dict):
        return payload
    return {"raw_data": str(payload)}


def record_contact_inquiry(
    lead: Lead,
    payload: Union[Dict[str, Any], str],
) -> Optional[ContactInquiry]:
    """
    Saves dedicated contact form inquiry to ContactInquiry model schema,
    linking it to the parent Lead profile.
    
    Rule:
    'contact form ko alag model schema me rakho also put in leads schema too'
    """
    data = parse_payload(payload)
    attr = extract_attribution_from_dict(data)
    cust = extract_customer_from_dict(data)

    booking_id = cust["booking_id"]
    inquiry = None

    if booking_id:
        inquiry = ContactInquiry.objects.filter(booking_id=booking_id).first()

    if inquiry:
        inquiry.lead = lead
        if cust["name"]:
            inquiry.name = cust["name"]
        if cust["phone"]:
            inquiry.phone = cust["phone"]
        if cust["email"]:
            inquiry.email = cust["email"]
        if cust["address"]:
            inquiry.address = cust["address"]
        if cust["tv_brand"]:
            inquiry.tv_brand = cust["tv_brand"]
        if cust["screen_size"]:
            inquiry.screen_size = cust["screen_size"]
        if cust["problem_description"]:
            inquiry.problem_description = cust["problem_description"]
        if cust["scheduled_date"]:
            inquiry.preferred_date = cust["scheduled_date"]
        if cust["scheduled_slot"]:
            inquiry.preferred_time_slot = cust["scheduled_slot"]
        if cust["is_paid"]:
            inquiry.is_paid = True
            inquiry.amount = cust["amount"]
        if cust["order_id"]:
            inquiry.order_id = cust["order_id"]
        if cust["payment_id"]:
            inquiry.payment_id = cust["payment_id"]
        inquiry.raw_payload = data
        inquiry.save()
        logger.info("Updated existing ContactInquiry ID=%s (Booking: %s)", inquiry.id, booking_id)
        return inquiry

    inquiry = ContactInquiry.objects.create(
        lead=lead,
        name=cust["name"] or lead.name or "Contact Form Inquirer",
        phone=cust["phone"] or lead.phone or "",
        email=cust["email"] or lead.email,
        address=cust["address"],
        tv_brand=cust["tv_brand"] or cust["service_type"] or lead.service_type or "Multi-Brand",
        screen_size=cust["screen_size"],
        problem_description=cust["problem_description"] or lead.problem_description,
        preferred_date=cust["scheduled_date"],
        preferred_time_slot=cust["scheduled_slot"],
        booking_id=booking_id,
        status="pending",
        is_paid=cust["is_paid"],
        amount=cust["amount"],
        order_id=cust["order_id"],
        payment_id=cust["payment_id"],
        visitor_id=attr["visitor_id"] or lead.visitor_id,
        utm_source=attr["utm_source"] or lead.utm_source,
        utm_medium=attr["utm_medium"] or lead.utm_medium,
        utm_campaign=attr["utm_campaign"] or lead.utm_campaign,
        utm_term=attr["utm_term"] or lead.utm_term,
        utm_content=attr["utm_content"] or lead.utm_content,
        gclid=attr["gclid"] or lead.gclid,
        gad_source=attr["gad_source"] or lead.gad_source,
        gad_campaignid=attr["gad_campaignid"] or lead.gad_campaignid,
        gbraid=attr["gbraid"] or lead.gbraid,
        wbraid=attr["wbraid"] or lead.wbraid,
        fbclid=attr["fbclid"] or lead.fbclid,
        landing_page=attr["landing_page"] or lead.landing_page,
        referrer=attr["referrer"] or lead.referrer,
        raw_payload=data,
    )
    logger.info("Created dedicated ContactInquiry ID=%s linked to Lead ID=%s", inquiry.id, lead.id)
    return inquiry


def save_or_update_lead(
    payload: Union[Dict[str, Any], str],
    source_override: Optional[str] = None,
    event_type_override: Optional[str] = None,
) -> Lead:
    """
    Core function to save or update leads with returning visitor loyalty tracking.
    
    Rule:
    "for a person who has already visited uska counter ++ kro taki pta lage most loyal user"
    
    If the visitor has previously landed or interacted (matched via visitor_id, phone, or email):
      - Increments visit_count counter (++).
      - Updates last_visited_at.
      - Merges latest customer contact information & service brief.
      - Updates latest campaign / ad click attribution touchpoint.
    Otherwise:
      - Creates a new Lead with visit_count = 1.
    """
    data = parse_payload(payload)
    attr = extract_attribution_from_dict(data)
    cust = extract_customer_from_dict(data)

    source = source_override or data.get("source") or "ronak_electronics_web"
    event_type = event_type_override or data.get("event") or data.get("event_type") or "tv_repair_inquiry"

    visitor_id = attr["visitor_id"]
    phone = cust["phone"]
    email = cust["email"]

    # Look for existing returning user by visitor_id, phone, or email
    existing_lead: Optional[Lead] = None

    if visitor_id:
        existing_lead = Lead.objects.filter(visitor_id=visitor_id).order_by("-updated_at").first()

    if not existing_lead and phone:
        existing_lead = Lead.objects.filter(phone=phone).order_by("-updated_at").first()

    if not existing_lead and email:
        existing_lead = Lead.objects.filter(email=email).order_by("-updated_at").first()

    now = timezone.now()

    if existing_lead:
        # User is returning! Increment loyal visit counter ++
        existing_lead.visit_count = (existing_lead.visit_count or 1) + 1
        existing_lead.last_visited_at = now

        # Upgrade source/event_type if user performed a higher-intent action
        HIGH_INTENT_SOURCES = ("phone_call", "whatsapp_click", "tv_repair_inquiry", "google_one_tap")
        if source in HIGH_INTENT_SOURCES or existing_lead.source in ("web_visit", ""):
            existing_lead.source = source
            existing_lead.event_type = event_type

        # Update customer profile if new info provided
        GENERIC_VISITOR_NAMES = ("Website Inquirer", "Website Visitor", "Direct Web Visitor", "Google User", "")
        if cust["name"] and cust["name"] not in GENERIC_VISITOR_NAMES:
            # New name is a real customer name, Google name, or detailed attribution name
            existing_lead.name = cust["name"]
        elif cust["name"] and existing_lead.name in GENERIC_VISITOR_NAMES:
            existing_lead.name = cust["name"]

        if phone and not existing_lead.phone:
            existing_lead.phone = phone
        elif phone:
            existing_lead.phone = phone

        if email and not existing_lead.email:
            existing_lead.email = email

        if visitor_id and not existing_lead.visitor_id:
            existing_lead.visitor_id = visitor_id

        if cust["problem_description"]:
            existing_lead.problem_description = cust["problem_description"]

        if cust["service_type"]:
            existing_lead.service_type = cust["service_type"]

        if cust["booking_id"]:
            existing_lead.booking_id = cust["booking_id"]

        if cust["is_paid"]:
            existing_lead.is_paid = True
            existing_lead.amount = cust["amount"]

        # Update campaign attribution if a new ad/campaign touchpoint occurred
        if attr["utm_source"]:
            existing_lead.utm_source = attr["utm_source"]
        if attr["utm_medium"]:
            existing_lead.utm_medium = attr["utm_medium"]
        if attr["utm_campaign"]:
            existing_lead.utm_campaign = attr["utm_campaign"]
        if attr["utm_term"]:
            existing_lead.utm_term = attr["utm_term"]
        if attr["utm_content"]:
            existing_lead.utm_content = attr["utm_content"]
        if attr["gclid"]:
            existing_lead.gclid = attr["gclid"]
        if attr["gad_source"]:
            existing_lead.gad_source = attr["gad_source"]
        if attr["gad_campaignid"]:
            existing_lead.gad_campaignid = attr["gad_campaignid"]
        if attr["gbraid"]:
            existing_lead.gbraid = attr["gbraid"]
        if attr["wbraid"]:
            existing_lead.wbraid = attr["wbraid"]
        if attr["fbclid"]:
            existing_lead.fbclid = attr["fbclid"]
        if attr["landing_page"]:
            existing_lead.landing_page = attr["landing_page"]
        if attr["referrer"]:
            existing_lead.referrer = attr["referrer"]

        # Preserve latest raw payload
        existing_lead.raw_payload = data
        existing_lead.save()
        logger.info(
            "Returning loyal visitor detected: ID=%s Name=%s Phone=%s Source=%s (Total visits: %s)",
            existing_lead.id,
            existing_lead.name,
            existing_lead.phone,
            existing_lead.source,
            existing_lead.visit_count,
        )

        # If payload contains contact form details, also record in dedicated ContactInquiry schema
        if phone or cust["booking_id"] or cust["address"]:
            try:
                record_contact_inquiry(existing_lead, data)
            except Exception as inquiry_err:
                logger.warning("Error recording contact inquiry: %s", inquiry_err)

        # Trigger Firebase push alert if customer submitted contact info or clicked high-intent CTA
        if phone or cust["booking_id"] or source in ("phone_call", "whatsapp_click", "tv_repair_inquiry"):
            try:
                notify_new_lead_fcm(existing_lead)
            except Exception as fcm_err:
                logger.warning("FCM notification skipped: %s", fcm_err)

        return existing_lead

    # Create brand new Lead
    new_lead = Lead.objects.create(
        name=cust["name"],
        phone=phone,
        email=email,
        problem_description=cust["problem_description"],
        service_type=cust["service_type"],
        source=source,
        event_type=event_type,
        booking_id=cust["booking_id"],
        is_paid=cust["is_paid"],
        amount=cust["amount"],
        visitor_id=visitor_id,
        visit_count=1,
        last_visited_at=now,
        utm_source=attr["utm_source"],
        utm_medium=attr["utm_medium"],
        utm_campaign=attr["utm_campaign"],
        utm_term=attr["utm_term"],
        utm_content=attr["utm_content"],
        gclid=attr["gclid"],
        gad_source=attr["gad_source"],
        gad_campaignid=attr["gad_campaignid"],
        gbraid=attr["gbraid"],
        wbraid=attr["wbraid"],
        fbclid=attr["fbclid"],
        landing_page=attr["landing_page"],
        referrer=attr["referrer"],
        raw_payload=data,
    )
    logger.info("New lead created: ID=%s Name=%s Phone=%s", new_lead.id, new_lead.name, new_lead.phone)

    # If payload contains contact form details, also record in dedicated ContactInquiry schema
    if phone or cust["booking_id"] or cust["address"]:
        try:
            record_contact_inquiry(new_lead, data)
        except Exception as inquiry_err:
            logger.warning("Error recording contact inquiry: %s", inquiry_err)

    # Trigger Firebase push alert if customer submitted contact info or clicked high-intent CTA
    if phone or cust["booking_id"] or source in ("phone_call", "whatsapp_click", "tv_repair_inquiry"):
        try:
            notify_new_lead_fcm(new_lead)
        except Exception as fcm_err:
            logger.warning("FCM notification skipped: %s", fcm_err)

    return new_lead


def get_loyal_users(min_visits: int = 2, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Returns loyal returning visitors who visited multiple times.
    "for a person who has already visited uska counter ++ kro taki pta lage most loyal user"
    """
    loyal_leads = (
        Lead.objects.filter(visit_count__gte=min_visits)
        .order_by("-visit_count", "-last_visited_at")[:limit]
    )

    return [
        {
            "id": lead.id,
            "name": lead.name,
            "phone": lead.phone,
            "email": lead.email,
            "visit_count": lead.visit_count,
            "visitor_id": lead.visitor_id,
            "booking_id": lead.booking_id,
            "status": lead.status,
            "service_type": lead.service_type,
            "utm_campaign": lead.utm_campaign,
            "utm_source": lead.utm_source,
            "gclid": lead.gclid,
            "last_visited_at": lead.last_visited_at.isoformat() if lead.last_visited_at else None,
            "created_at": lead.created_at.isoformat() if lead.created_at else None,
        }
        for lead in loyal_leads
    ]


def get_campaign_analytics() -> Dict[str, Any]:
    """
    Aggregates marketing campaign and ad channel statistics.
    Groups leads by utm_campaign, utm_source, gclid, and meta ads.
    """
    total_leads = Lead.objects.count()
    total_visits = Lead.objects.aggregate(total=Sum("visit_count"))["total"] or total_leads

    # Group by UTM campaign
    campaign_counts = (
        Lead.objects.exclude(Q(utm_campaign__isnull=True) | Q(utm_campaign=""))
        .values("utm_campaign")
        .annotate(leads_count=Count("id"), total_visits=Sum("visit_count"))
        .order_by("-leads_count")[:20]
    )

    # Group by UTM source
    source_counts = (
        Lead.objects.exclude(Q(utm_source__isnull=True) | Q(utm_source=""))
        .values("utm_source")
        .annotate(leads_count=Count("id"))
        .order_by("-leads_count")[:15]
    )

    # Google Ads and Meta Ads counts
    google_ads_leads = Lead.objects.filter(Q(gclid__isnull=False) & ~Q(gclid="")).count()
    meta_ads_leads = Lead.objects.filter(Q(fbclid__isnull=False) & ~Q(fbclid="")).count()

    return {
        "total_leads": total_leads,
        "total_visits": total_visits,
        "google_ads_leads": google_ads_leads,
        "meta_ads_leads": meta_ads_leads,
        "top_campaigns": list(campaign_counts),
        "top_sources": list(source_counts),
    }


def list_leads_data(
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Returns sanitized list of leads for dashboard / admin consumption.
    """
    qs = Lead.objects.all().order_by("-created_at")

    if status:
        qs = qs.filter(status=status.strip().lower())

    if search:
        s = search.strip()
        qs = qs.filter(
            Q(name__icontains=s)
            | Q(phone__icontains=s)
            | Q(email__icontains=s)
            | Q(booking_id__icontains=s)
            | Q(problem_description__icontains=s)
        )

    leads = qs[offset : offset + limit]

    return [
        {
            "id": l.id,
            "name": l.name,
            "phone": l.phone,
            "email": l.email,
            "problem": l.problem_description,
            "service_type": l.service_type,
            "status": l.status,
            "booking_id": l.booking_id,
            "is_paid": l.is_paid,
            "amount": float(l.amount),
            "visit_count": l.visit_count,
            "visitor_id": l.visitor_id,
            "utm_campaign": l.utm_campaign,
            "utm_source": l.utm_source,
            "gclid": l.gclid,
            "created_at": l.created_at.isoformat() if l.created_at else None,
            "last_visited_at": l.last_visited_at.isoformat() if l.last_visited_at else None,
        }
        for l in leads
    ]


def list_contact_inquiries_data(
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Returns sanitized list of contact form inquiries from ContactInquiry model schema.
    """
    qs = ContactInquiry.objects.all().order_by("-created_at")

    if status:
        qs = qs.filter(status=status.strip().lower())

    if search:
        s = search.strip()
        qs = qs.filter(
            Q(name__icontains=s)
            | Q(phone__icontains=s)
            | Q(email__icontains=s)
            | Q(booking_id__icontains=s)
            | Q(tv_brand__icontains=s)
            | Q(address__icontains=s)
            | Q(problem_description__icontains=s)
        )

    inquiries = qs[offset : offset + limit]

    return [
        {
            "id": inq.id,
            "lead_id": inq.lead_id,
            "name": inq.name,
            "phone": inq.phone,
            "email": inq.email,
            "address": inq.address,
            "tv_brand": inq.tv_brand,
            "screen_size": inq.screen_size,
            "problem": inq.problem_description,
            "preferred_date": inq.preferred_date,
            "preferred_time_slot": inq.preferred_time_slot,
            "booking_id": inq.booking_id,
            "status": inq.status,
            "is_paid": inq.is_paid,
            "amount": float(inq.amount),
            "order_id": inq.order_id,
            "payment_id": inq.payment_id,
            "visitor_id": inq.visitor_id,
            "utm_campaign": inq.utm_campaign,
            "utm_source": inq.utm_source,
            "gclid": inq.gclid,
            "created_at": inq.created_at.isoformat() if inq.created_at else None,
        }
        for inq in inquiries
    ]
