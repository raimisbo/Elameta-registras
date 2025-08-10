# detaliu_registras/admin.py
from django.contrib import admin
from .models import Klientas, Projektas, Detale, Kaina, Danga, Uzklausa

@admin.register(Klientas)
class KlientasAdmin(admin.ModelAdmin):
    list_display = ("vardas", "telefonas", "email")
    search_fields = ("vardas", "telefonas", "email")

@admin.register(Projektas)
class ProjektasAdmin(admin.ModelAdmin):
    list_display = ("pavadinimas", "klientas", "uzklausos_data", "pasiulymo_data")
    list_filter = ("uzklausos_data", "pasiulymo_data")
    search_fields = ("pavadinimas", "klientas__vardas")

@admin.register(Detale)
class DetaleAdmin(admin.ModelAdmin):
    # jokių filter_horizontal (nes nėra M2M laukų)
    list_display = ("pavadinimas", "brezinio_nr", "kiekis_menesis", "danga")
    list_filter = ("danga",)
    search_fields = ("pavadinimas", "brezinio_nr")

@admin.register(Kaina)
class KainaAdmin(admin.ModelAdmin):
    list_display = ("detale", "kaina_nuo", "kaina_iki", "suma", "kainos_matas")
    list_filter = ("kainos_matas",)
    search_fields = ("detale__pavadinimas",)

@admin.register(Danga)
class DangaAdmin(admin.ModelAdmin):
    list_display = ("pavadinimas",)
    search_fields = ("pavadinimas",)

@admin.register(Uzklausa)
class UzklausaAdmin(admin.ModelAdmin):
    list_display = ("id", "klientas", "projektas", "detale")
    search_fields = ("klientas__vardas", "projektas__pavadinimas", "detale__pavadinimas")
