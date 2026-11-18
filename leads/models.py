from django.db import models


class Lead(models.Model):
    STATUS_CHOICES = [
        ("new", "New Inquiry"),
        ("contacted", "Contacted / Called"),
        ("technician_dispatched", "Technician Dispatched"),
        ("in_repair", "In Repair at Service Center"),
        ("completed", "Completed / Delivered"),
        ("cancelled", "Cancelled"),
    ]

    # Primary customer details
    name = models.CharField(max_length=255, db_index=True)
    phone = models.CharField(max_length=50, db_index=True)
    email = models.EmailField(blank=True, null=True)

    # Lead problem & service
    problem_description = models.TextField(blank=True, default="")
    service_type = models.CharField(max_length=150, blank=True, default="")
    service_center = models.CharField(
        max_length=255,
        default="Ronak Electronics Service Center, Surat",
    )

    # Funnel & Event metadata
    source = models.CharField(max_length=100, default="ronak_electronics_funnel")
    event_type = models.CharField(max_length=100, default="tv_repair_inquiry")
    booking_id = models.CharField(max_length=100, blank=True, db_index=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="new")

    # Payment tracking (for Razorpay toggle)
    is_paid = models.BooleanField(default=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Full raw JSON payload (preserves any arbitrary JSON sent by frontend)
    raw_payload = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Lead"
        verbose_name_plural = "Leads"

    def __str__(self):
        ref = self.booking_id or f"ID-{self.id}"
        return f"[{ref}] {self.name} ({self.phone}) - {self.get_status_display()}"
