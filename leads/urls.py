from django.urls import path
from . import views

urlpatterns = [
    # TV Repair Booking (supports both /api/webhooks/tv-repair/ and /api/leads/booking/)
    path("webhooks/tv-repair/", views.tv_repair_webhook, name="tv_repair_webhook"),
    path("leads/booking/", views.tv_repair_webhook, name="leads_booking"),
    # Page Visit & Loyal Visitor Tracking Beacon
    path("leads/visit/", views.page_visit_beacon, name="page_visit_beacon"),
    # Call Click, WhatsApp Click & Interaction Lead Beacon
    path("leads/event/", views.lead_event_api, name="lead_event_api"),
    # Google One Tap / Google Sign-in Lead Capture
    path("leads/google-sync/", views.google_sync_lead, name="google_sync_lead"),
    # General Lead Webhook
    path("webhooks/lead/", views.generic_lead_webhook, name="generic_lead_webhook"),
    # Loyal Returning Users API (visit_count >= 2)
    path("leads/loyal-users/", views.loyal_users_api, name="loyal_users_api"),
    # Marketing Campaign & Ad Attribution Analytics API
    path("leads/campaigns/", views.campaign_analytics_api, name="campaign_analytics_api"),
    # Leads List API
    path("leads/", views.lead_list_api, name="lead_list_api"),
    # Dedicated Contact Form Inquiries List API
    path("contact-inquiries/", views.contact_inquiries_api, name="contact_inquiries_api"),
    # Firebase Cloud Messaging Token Registration
    path("notifications/register-token/", views.register_fcm_token_api, name="register_fcm_token_api"),
]
