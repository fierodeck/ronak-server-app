from django.contrib import admin
from .models import WhatsAppMessageLog


@admin.register(WhatsAppMessageLog)
class WhatsAppMessageLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "phone",
        "recipient_name",
        "template_type",
        "status",
        "booking_id",
        "lead_link",
        "created_at",
    )
    list_filter = ("status", "template_type", "created_at")
    search_fields = ("phone", "recipient_name", "booking_id", "message_body", "whatsapp_message_id")
    readonly_fields = ("created_at", "updated_at", "payload", "provider_response")
    list_per_page = 25

    def lead_link(self, obj):
        if obj.lead:
            return f"Lead #{obj.lead.id} ({obj.lead.name})"
        return "-"
    lead_link.short_description = "Associated Lead"
