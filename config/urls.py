from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.views.generic.base import RedirectView


def index_view(request):
    return JsonResponse({
        "service": "Ronak Electronics Lead Generation API",
        "status": "online",
        # "database": "sqlite3",
        # "endpoints": {
        #     "tv_repair_webhook": "/api/webhooks/tv-repair/",
        #     "generic_lead_webhook": "/api/webhooks/lead/",
        #     "leads_list": "/api/leads/",
        #     "admin_dashboard": "/admin/",
        # }
    })

api_v1 = [
    path("", include("leads.urls")),
    path("", include("whatsapp.urls")),
]

urlpatterns = [
    path("api/", include(api_v1)),
    path("api/v1/", include(api_v1)),
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
]
