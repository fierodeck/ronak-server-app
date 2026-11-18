from django.urls import path
from . import views

urlpatterns = [
    # TV Repair Webhook matching DJANGO_BACKEND_WEBHOOK_URL: http://localhost:8000/api/webhooks/tv-repair/
    path("webhooks/tv-repair/", views.tv_repair_webhook, name="tv_repair_webhook"),
    # General Lead Webhook
    path("webhooks/lead/", views.generic_lead_webhook, name="generic_lead_webhook"),
    # Simple JSON list of leads
    path("leads/", views.lead_list_api, name="lead_list_api"),
]
