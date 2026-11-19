from django.urls import path
from . import views

urlpatterns = [
    # Trigger WhatsApp message by template type or custom body
    path("whatsapp/send/", views.trigger_message_api, name="whatsapp_send"),
    # Audit log of WhatsApp messages
    path("whatsapp/logs/", views.list_messages_api, name="whatsapp_logs"),
    # Available templates directory
    path("whatsapp/templates/", views.list_templates_api, name="whatsapp_templates"),
    # Meta WhatsApp Cloud API Webhook
    path("whatsapp/webhook/", views.whatsapp_webhook_api, name="whatsapp_webhook"),
]
