from django.contrib import admin
from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "phone",
        "status",
        "booking_id",
        "service_type",
        "service_center",
        "is_paid",
        "created_at",
    )
    list_filter = ("status", "source", "event_type", "is_paid", "created_at")
    search_fields = ("name", "phone", "booking_id", "problem_description")
    readonly_fields = ("created_at", "updated_at", "raw_payload")
    list_editable = ("status",)
    list_per_page = 25
