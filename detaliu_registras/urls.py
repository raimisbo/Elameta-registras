from django.urls import path
from . import views

app_name = "detaliu_registras"  # Add namespace

urlpatterns = [
    # Dashboard
    path("", views.IndexView.as_view(), name="index"),
    # Requests (Uzklausos) - RESTful patterns
    path("uzklausos/", views.UzklausaListView.as_view(), name="uzklausa_list"),
    path(
        "uzklausos/naujas/", views.UzklausaCreateView.as_view(), name="uzklausa_create"
    ),
    path(
        "uzklausos/<int:pk>/",
        views.UzklausaDetailView.as_view(),
        name="uzklausa_detail",
    ),
    # path('uzklausos/<int:pk>/redaguoti/', views.UzklausaUpdateView.as_view(), name='uzklausa_update'),
    # Prices (Kainos)
    # path('uzklausos/<int:uzklausa_pk>/kainos/', views.KainaListView.as_view(), name='kaina_list'),
    path(
        "uzklausos/<int:uzklausa_pk>/kainos/redaguoti/",
        views.KainaUpdateView.as_view(),
        name="kaina_update",
    ),
    # Client requests by client
    path(
        "klientai/<int:klientas_id>/uzklausos/",
        views.KlientoUzklausosView.as_view(),
        name="kliento_uzklausos",
    ),
    # Utilities
    path("import_csv/", views.ImportCSVView.as_view(), name="import_csv"),
]
