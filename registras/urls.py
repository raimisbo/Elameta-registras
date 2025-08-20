from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework import routers
from detaliu_registras.api import DetaleViewSet

router = routers.DefaultRouter()
router.register(r"detales", DetaleViewSet, basename="detales")

urlpatterns = [

    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),

    # visi app'o maršrutai po /detaliu_registras/
    path(
        "detaliu_registras/",
        include(("detaliu_registras.urls", "detaliu_registras"), namespace="detaliu_registras"),
    ),

    # šaknį / nukreipiam į app'o index
    path("", RedirectView.as_view(pattern_name="detaliu_registras:index", permanent=False)),
]
