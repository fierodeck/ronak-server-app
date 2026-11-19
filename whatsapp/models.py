from django.db import models


class WhatsAppMessageLog(models.Model):
    """
    Audit log of all WhatsApp messages created or triggered.
    Tracks template type, rendered content, recipient, delivery status, and provider responses.
    """
    STATUS_CHOICES = [
        ("prepared", "Prepared / Dry-Run"),
        ("queued", "Queued"),
        ("sent", "Sent"),
        ("delivered", "Delivered"),
        ("read", "Read by Customer"),
        ("failed", "Failed to Send"),
    ]

    # Recipient
    phone = models.CharField(max_length=50, db_index=True)
    recipient_name = models.CharField(max_length=255, blank=True, default="Customer")

    # Template & Message Content
    template_type = models.CharField(max_length=100, db_index=True)
    message_body = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="prepared", db_index=True)

    # Lead & Booking Relationships (Optional)
    lead = models.ForeignKey("leads.Lead", on_delete=models.SET_NULL, null=True, blank=True, related_name="whatsapp_messages",)
    booking_id = models.CharField(max_length=100, blank=True, default="", db_index=True)

    # Provider metadata (e.g. Meta Graph API message ID)
    whatsapp_message_id = models.CharField(max_length=150, blank=True, default="", db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    provider_response = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, default="")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "WhatsApp Message Log"
        verbose_name_plural = "WhatsApp Message Logs"

    def __str__(self):
        return f"[{self.template_type}] {self.phone} - {self.get_status_display()}"
