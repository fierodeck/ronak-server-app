from django.contrib import admin
from .models import Lead, ContactInquiry, FCMDeviceToken


admin.site.site_header = "Ronak Electronics Lead Generation Admin"
admin.site.site_title = "Ronak Electronics Lead Generation Admin"
admin.site.index_title = "Lead Generation Admin Dashboard"


class ContactInquiryInline(admin.TabularInline):
    model = ContactInquiry
    extra = 0
    readonly_fields = (
        "booking_id",
        "name",
        "phone",
        "tv_brand",
        "problem_description",
        "preferred_date",
        "preferred_time_slot",
        "is_paid",
        "created_at",
    )
    can_delete = False
    show_change_link = True


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "phone",
        "email",
        "source",
        "visit_count",
        "status",
        "booking_id",
        "utm_campaign",
        "utm_source",
        "gclid",
        "is_paid",
        "created_at",
        "last_visited_at",
    )
    list_filter = ("status", "visit_count", "source", "utm_campaign", "utm_source", "is_paid", "created_at")
    search_fields = ("name", "phone", "email", "booking_id", "visitor_id", "utm_campaign", "gclid")
    readonly_fields = ("created_at", "updated_at", "last_visited_at", "raw_payload")
    list_editable = ("status",)
    inlines = [ContactInquiryInline]
    list_per_page = 25


@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "booking_id",
        "name",
        "phone",
        "tv_brand",
        "status",
        "preferred_date",
        "preferred_time_slot",
        "is_paid",
        "lead_link",
        "created_at",
    )
    list_filter = ("status", "tv_brand", "is_paid", "preferred_date", "created_at")
    search_fields = ("name", "phone", "email", "booking_id", "address", "tv_brand", "visitor_id")
    readonly_fields = ("created_at", "updated_at", "raw_payload")
    list_editable = ("status",)
    list_per_page = 25

    def lead_link(self, obj):
        if obj.lead:
            return f"Lead #{obj.lead.id} ({obj.lead.name})"
        return "-"
    lead_link.short_description = "Associated Lead"


@admin.register(FCMDeviceToken)
class FCMDeviceTokenAdmin(admin.ModelAdmin):
    list_display = ("id", "device_name", "role", "is_active", "token_preview", "updated_at")
    list_filter = ("role", "is_active", "created_at")
    search_fields = ("device_name", "token", "role")
    list_editable = ("is_active",)

    def token_preview(self, obj):
        return f"{obj.token[:16]}...{obj.token[-8:]}" if len(obj.token) > 24 else obj.token
    token_preview.short_description = "Token"
