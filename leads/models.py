from django.db import models
from django.utils import timezone


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
    phone = models.CharField(max_length=50, blank=True, db_index=True)
    email = models.EmailField(blank=True, null=True, db_index=True)

    # Lead problem & service
    problem_description = models.TextField(blank=True, default="")
    service_type = models.CharField(max_length=150, blank=True, default="")
    service_center = models.CharField(
        max_length=255,
        default="Ronak Electronics Service Center, Surat",
    )

    # Funnel & Event metadata
    source = models.CharField(max_length=100, default="ronak_electronics_web", db_index=True)
    event_type = models.CharField(max_length=100, default="tv_repair_inquiry")
    booking_id = models.CharField(max_length=100, blank=True, db_index=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="new", db_index=True)

    # Payment tracking (for Razorpay toggle)
    is_paid = models.BooleanField(default=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Visitor Loyalty & Return Frequency Tracking
    # "for a person who has already visited uska counter ++ kro taki pta lage most loyal user"
    visitor_id = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    visit_count = models.IntegerField(default=1, db_index=True)
    last_visited_at = models.DateTimeField(default=timezone.now, db_index=True)

    # Marketing Campaign & Ad Source Attribution
    # Tracks Google Ads (gclid, gad_source, gad_campaignid, gbraid, wbraid), Meta Ads (fbclid), UTM parameters & Landing Pages
    utm_source = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    utm_medium = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    utm_campaign = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    utm_term = models.CharField(max_length=255, blank=True, null=True)
    utm_content = models.CharField(max_length=255, blank=True, null=True)
    gclid = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    gad_source = models.CharField(max_length=50, blank=True, null=True)
    gad_campaignid = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    gbraid = models.CharField(max_length=255, blank=True, null=True)
    wbraid = models.CharField(max_length=255, blank=True, null=True)
    fbclid = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    landing_page = models.CharField(max_length=500, blank=True, null=True)
    referrer = models.CharField(max_length=500, blank=True, null=True)

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
        return f"[{ref}] {self.name} (Visits: {self.visit_count}) - {self.get_status_display()}"


class ContactInquiry(models.Model):
    """
    Dedicated model schema for Customer Contact Form and Doorstep Repair Inquiries.
    Stores complete form submissions including television brand, screen size, doorstep address,
    appointment date & time slot, and payment references.
    Linked to the central Lead profile.
    """
    STATUS_CHOICES = [
        ("pending", "Pending Callback"),
        ("contacted", "Customer Contacted"),
        ("scheduled", "Visit Scheduled"),
        ("in_repair", "In Repair at Service Center"),
        ("completed", "Completed / Delivered"),
        ("cancelled", "Cancelled"),
    ]

    # Link to unified Lead profile
    lead = models.ForeignKey(
        Lead,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contact_inquiries",
    )

    # Customer Identity
    name = models.CharField(max_length=255, db_index=True)
    phone = models.CharField(max_length=50, db_index=True)
    email = models.EmailField(blank=True, null=True, db_index=True)
    address = models.TextField(blank=True, default="")

    # TV & Service Details
    tv_brand = models.CharField(max_length=150, blank=True, default="Multi-Brand")
    screen_size = models.CharField(max_length=100, blank=True, default="")
    problem_description = models.TextField(blank=True, default="")
    preferred_date = models.CharField(max_length=50, blank=True, default="")
    preferred_time_slot = models.CharField(max_length=100, blank=True, default="")

    # Booking & Status
    booking_id = models.CharField(max_length=100, blank=True, db_index=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="pending", db_index=True)

    # Payment (Razorpay toggle)
    is_paid = models.BooleanField(default=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    order_id = models.CharField(max_length=100, blank=True, default="")
    payment_id = models.CharField(max_length=100, blank=True, default="")

    # Marketing Attribution & Visitor Tracking
    visitor_id = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    utm_source = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    utm_medium = models.CharField(max_length=100, blank=True, null=True)
    utm_campaign = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    utm_term = models.CharField(max_length=255, blank=True, null=True)
    utm_content = models.CharField(max_length=255, blank=True, null=True)
    gclid = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    gad_source = models.CharField(max_length=50, blank=True, null=True)
    gad_campaignid = models.CharField(max_length=100, blank=True, null=True)
    gbraid = models.CharField(max_length=255, blank=True, null=True)
    wbraid = models.CharField(max_length=255, blank=True, null=True)
    fbclid = models.CharField(max_length=255, blank=True, null=True)
    landing_page = models.CharField(max_length=500, blank=True, null=True)
    referrer = models.CharField(max_length=500, blank=True, null=True)

    # Full raw JSON payload
    raw_payload = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Contact Form Inquiry"
        verbose_name_plural = "Contact Form Inquiries"

    def __str__(self):
        ref = self.booking_id or f"ID-{self.id}"
        return f"[{ref}] {self.name} ({self.phone}) - {self.tv_brand} - {self.get_status_display()}"


# Model Alias
ContactForm = ContactInquiry


class FCMDeviceToken(models.Model):
    """
    Stores Firebase Cloud Messaging (FCM) device tokens for technicians and service center admins.
    Used to dispatch instant push notifications when repair leads and bookings arrive.
    """
    token = models.CharField(max_length=255, unique=True, db_index=True)
    device_name = models.CharField(max_length=150, blank=True, default="Technician Phone")
    role = models.CharField(max_length=50, default="technician", db_index=True)  # technician, admin, service_center
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "FCM Device Token"
        verbose_name_plural = "FCM Device Tokens"

    def __str__(self):
        return f"{self.device_name} ({self.role}) - {'Active' if self.is_active else 'Inactive'}"
