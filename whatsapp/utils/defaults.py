"""
Default WhatsApp message templates for Ronak Electronics.
Placeholders format: {name}, {booking_id}, {tv_brand}, {date}, {time_slot}, {address}, etc.
"""

DEFAULT_TEMPLATES = {
    "lead_welcome": {
        "title": "Lead Welcome & Inquiry Acknowledgement",
        "category": "transactional",
        "description": "Triggered when a customer lands and submits an inquiry",
        "body": (
            "Namaste {name}! 🙏\n\n"
            "Thank you for contacting *Ronak Electronics* — Surat's trusted TV Repair & Service Specialist.\n\n"
            "We have received your repair inquiry:\n"
            "📺 *Issue / Service:* {problem}\n\n"
            "Our senior technician is reviewing your request and will call you within 15 minutes.\n\n"
            "📍 *Main Workshop:* Ronak Electronics, Anand Mahal Road, Adajan, Surat\n"
            "📞 *Direct Helpline:* +91 98986 47777"
        ),
    },
    "booking_confirmation": {
        "title": "Doorstep TV Repair Booking Confirmation",
        "category": "transactional",
        "description": "Triggered when doorstep technician visit is booked",
        "body": (
            "✅ *TV Repair Doorstep Booking Confirmed!*\n\n"
            "Dear {name},\n\n"
            "Your doorstep inspection appointment is confirmed:\n"
            "🔖 *Booking Reference:* {booking_id}\n"
            "📺 *TV Model / Brand:* {tv_brand} {screen_size}\n"
            "📅 *Date:* {date}\n"
            "⏰ *Time Slot:* {time_slot}\n"
            "📍 *Address:* {address}\n\n"
            "Our certified technician will arrive on time with diagnostics tools & genuine spares.\n"
            "📞 Need to reschedule? Call +91 98986 47777"
        ),
    },
    "visiting_fee_paid": {
        "title": "Advance Visiting Fee Payment Receipt",
        "category": "transactional",
        "description": "Triggered when visiting deposit is paid via Razorpay",
        "body": (
            "💳 *Payment Received — Priority Booking Activated!*\n\n"
            "Dear {name},\n\n"
            "We have received your advance inspection deposit:\n"
            "💰 *Amount Paid:* ₹{amount}\n"
            "🔖 *Booking Reference:* {booking_id}\n"
            "🧾 *Payment ID:* {payment_id}\n\n"
            "Your appointment for {date} ({time_slot}) is locked with a Senior Engineer. "
            "This fee is 100% adjusted against the final repair bill.\n\n"
            "Thank you for choosing Ronak Electronics!"
        ),
    },
    "technician_dispatched": {
        "title": "Technician Dispatched to Doorstep",
        "category": "alert",
        "description": "Triggered when technician departs for customer doorstep",
        "body": (
            "🚀 *Technician On The Way!*\n\n"
            "Dear {name},\n\n"
            "Our technician is on the way to your address for Booking #{booking_id}:\n"
            "👨‍🔧 *Technician:* {technician_name}\n"
            "📞 *Mobile:* {technician_phone}\n"
            "⏱️ *Estimated Arrival:* {eta}\n\n"
            "Please ensure someone is available at the doorstep."
        ),
    },
    "repair_status_update": {
        "title": "Repair Status Progress Update",
        "category": "support",
        "description": "Triggered during diagnosis, parts replacement, or testing",
        "body": (
            "🔧 *TV Repair Status Update*\n\n"
            "Dear {name},\n\n"
            "Status update for your {tv_brand} ({booking_id}):\n"
            "📊 *Status:* {status_text}\n"
            "📝 *Technician Note:* {notes}\n"
            "⏱️ *Estimated Ready Date:* {estimated_delivery}\n\n"
            "We test every TV with professional color-bar test signals before delivery."
        ),
    },
    "repair_completed": {
        "title": "Repair Completed & Tested Notification",
        "category": "transactional",
        "description": "Triggered when TV is repaired, tested, and ready",
        "body": (
            "🎉 *TV Repair Completed & 100% Tested!*\n\n"
            "Dear {name},\n\n"
            "Great news! Your {tv_brand} has been successfully repaired and passed all quality tests.\n"
            "🔖 *Booking ID:* {booking_id}\n"
            "💵 *Total Bill:* ₹{amount}\n"
            "🛡️ *Warranty Guarantee:* {warranty_period}\n\n"
            "Thank you for choosing Ronak Electronics Surat!"
        ),
    },
    "call_click_acknowledgement": {
        "title": "Call Click / Callback Request",
        "category": "transactional",
        "description": "Triggered when customer clicks call on website",
        "body": (
            "📞 *Thank You for Reaching Out to Ronak Electronics!*\n\n"
            "Hello {name},\n\n"
            "We noticed you requested a call or tried contacting us regarding TV repair.\n"
            "Our senior engineer is reviewing your request and will call you right away.\n\n"
            "💬 You can also reply directly here with your TV brand and issue for instant pricing!"
        ),
    },
    "lead_followup": {
        "title": "Marketing / Inquiry Follow-Up",
        "category": "marketing",
        "description": "Follow-up for inquirers who haven't confirmed booking",
        "body": (
            "👋 *Need Help with Your TV? — Ronak Electronics Surat*\n\n"
            "Hello {name},\n\n"
            "Are you still looking to get your TV repaired?\n"
            "We offer:\n"
            "✨ *Same-Day Doorstep Service* across Surat\n"
            "✨ *100% Genuine Spare Parts* (Panel, Motherboard, Power Supply)\n"
            "✨ *Up to 90 Days Service Warranty*\n\n"
            "Reply 'BOOK' to this message to lock your technician slot today!"
        ),
    },
    "custom": {
        "title": "Custom Direct Message",
        "category": "support",
        "description": "Custom message body provided dynamically at trigger time",
        "body": "{message_body}",
    },
}
