from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


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
    # path("", index_view, name="index"),
    # path("admin/", admin.site.urls),
    path("", admin.site.urls),
    path("api/v1/", include(api_v1)),

    path("api/", include(api_v1)),

]
