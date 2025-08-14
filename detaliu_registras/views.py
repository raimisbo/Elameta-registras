from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Q, Count
from django.contrib import messages
from django.forms import formset_factory
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date
import json
import logging

from .models import Klientas, Uzklausa
from .forms import (
    ImportCSVForm,
    UzklausaCreationForm,
    KainaForm,
    UzklausaFilterForm,
    DetaleForm,
    ProjektasForm,
)
from .services import UzklausaService
from .utils import import_csv

logger = logging.getLogger(__name__)


class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        klientu_duomenys = Uzklausa.objects.values(
            "klientas__vardas", "klientas__id"
        ).annotate(kiekis=Count("id"))

        context.update(
            {
                "uzklausos": Uzklausa.objects.all()[:10],
                "klientu_duomenys_json": json.dumps(list(klientu_duomenys)),
            }
        )
        return context


# --------- SERVER-SIDE FILTRUOJAMAS SĄRAŠAS ---------
class UzklausaListView(ListView):
    model = Uzklausa
    template_name = "detaliu_registras/uzklausa_list.html"
    context_object_name = "uzklausos"
    paginate_by = 20  # numatytasis

    def get_paginate_by(self, queryset):
        per_page = self.request.GET.get("per_page")
        try:
            return int(per_page) if per_page else self.paginate_by
        except (TypeError, ValueError):
            return self.paginate_by

    @staticmethod
    def _num(val):
        """Leidžia '12,5' ir '12.5'; tuščia -> None."""
        if val is None or val == "":
            return None
        try:
            return float(str(val).replace(",", "."))
        except ValueError:
            return None

    def get_queryset(self):
        p = self.request.GET
        used_m2m = False

        qs = (
            Uzklausa.objects
            .select_related("klientas", "projektas", "detale")
            .prefetch_related("detale__danga")
            .all()
            .order_by("-id")
        )

        # Greita laisvo teksto paieška (viršutinis 'q' laukas)
        q = (p.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(klientas__vardas__icontains=q)
                | Q(projektas__pavadinimas__icontains=q)
                | Q(detale__pavadinimas__icontains=q)
                | Q(detale__brezinio_nr__icontains=q)
            )

        # Tekstiniai filtrai
        text_map = {
            "f-klientas": "klientas__vardas__icontains",
            "f-projektas": "projektas__pavadinimas__icontains",
            "f-detale": "detale__pavadinimas__icontains",
            "f-brezinys": "detale__brezinio_nr__icontains",
            "f-danga": "detale__danga__pavadinimas__icontains",  # M2M
            "f-standartas": "detale__standartas__icontains",
            "f-kabinimo-tipas": "detale__kabinimo_tipas__icontains",
            "f-kabinimas-xyz": "detale__kabinimas_xyz__icontains",
            "f-pastabos": "detale__pastabos__icontains",
        }
        for key, lookup in text_map.items():
            v = (p.get(key) or "").strip()
            if v:
                qs = qs.filter(**{lookup: v})
                if "__danga__" in lookup:
                    used_m2m = True

        # Skaičių intervalai
        ranges = [
            ("f-metinis", "detale__kiekis_metinis"),
            ("f-menesis", "detale__kiekis_menesis"),
            ("f-partija", "detale__kiekis_partijai"),
            ("f-plotas", "detale__plotas"),
            ("f-svoris", "detale__svoris"),
            ("f-reme", "detale__kiekis_reme"),
            ("f-faktinis", "detale__faktinis_kiekis_reme"),
        ]
        for prefix, field in ranges:
            vmin = self._num(p.get(f"{prefix}-min"))
            vmax = self._num(p.get(f"{prefix}-max"))
            if vmin is not None:
                qs = qs.filter(**{f"{field}__gte": vmin})
            if vmax is not None:
                qs = qs.filter(**{f"{field}__lte": vmax})

        # Datos (nuo–iki)
        d1 = parse_date(p.get("f-uzklausa-from") or "")
        d2 = parse_date(p.get("f-uzklausa-to") or "")
        if d1:
            qs = qs.filter(projektas__uzklausos_data__date__gte=d1)
        if d2:
            qs = qs.filter(projektas__uzklausos_data__date__lte=d2)

        d3 = parse_date(p.get("f-pasiulymas-from") or "")
        d4 = parse_date(p.get("f-pasiulymas-to") or "")
        if d3:
            qs = qs.filter(projektas__pasiulymo_data__date__gte=d3)
        if d4:
            qs = qs.filter(projektas__pasiulymo_data__date__lte=d4)

        if used_m2m:
            qs = qs.distinct()

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Išlaikyti aktyvius GET filtrus paginacijoje
        params = self.request.GET.copy()
        params.pop("page", None)
        context["current_querystring"] = params.urlencode()
        # Jei naudoji filtrų formą – paliekam suderinamumui
        context["filter_form"] = UzklausaFilterForm(self.request.GET)
        return context
# -----------------------------------------------------


class UzklausaDetailView(DetailView):
    model = Uzklausa
    template_name = "detaliu_registras/uzklausa_detail.html"
    context_object_name = "uzklausa"

    def get_queryset(self):
        return Uzklausa.objects.select_related(
            "klientas", "projektas", "detale"
        ).prefetch_related("detale__kainos")


class UzklausaCreateView(TemplateView):
    template_name = "detaliu_registras/uzklausa_create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = UzklausaCreationForm()
        context["projektas_form"] = ProjektasForm()
        context["detale_form"] = DetaleForm()
        context["kaina_form"] = KainaForm()
        return context

    def post(self, request):
        form = UzklausaCreationForm(request.POST)
        projektas_form = ProjektasForm(request.POST)
        detale_form = DetaleForm(request.POST)
        kaina_form = KainaForm(request.POST)

        if all(
            [
                form.is_valid(),
                projektas_form.is_valid(),
                detale_form.is_valid(),
                kaina_form.is_valid(),
            ]
        ):
            try:
                uzklausa = UzklausaService.create_full_request(
                    form.cleaned_data, projektas_form, detale_form, kaina_form
                )
                messages.success(request, "Užklausa sėkmingai sukurta")
                return redirect("detaliu_registras:uzklausa_detail", pk=uzklausa.pk)
            except ValidationError as e:
                messages.error(request, f"Klaida: {e}")
        else:
            messages.error(request, "Formoje yra klaidų – patikrinkite visus laukus.")

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "projektas_form": projektas_form,
                "detale_form": detale_form,
                "kaina_form": kaina_form,
            },
        )


class KainaUpdateView(TemplateView):
    template_name = "detaliu_registras/kaina_update.html"

    def get(self, request, uzklausa_pk):
        uzklausa = get_object_or_404(Uzklausa, pk=uzklausa_pk)
        KainaFormSet = formset_factory(KainaForm, extra=1, can_delete=True)

        initial_data = [
            {
                "busena": k.busena,
                "suma": k.suma,
                "kiekis_nuo": k.kiekis_nuo,
                "kiekis_iki": k.kiekis_iki,
                "fiksuotas_kiekis": k.fiksuotas_kiekis,
                "kainos_matas": k.kainos_matas,
            }
            for k in uzklausa.detale.kainos.all()
        ]

        formset = KainaFormSet(initial=initial_data)

        return render(
            request,
            self.template_name,
            {
                "formset": formset,
                "uzklausa": uzklausa,
            },
        )

    def post(self, request, uzklausa_pk):
        uzklausa = get_object_or_404(Uzklausa, pk=uzklausa_pk)
        KainaFormSet = formset_factory(KainaForm, extra=1, can_delete=True)
        formset = KainaFormSet(request.POST)

        if formset.is_valid():
            UzklausaService.update_prices(uzklausa.detale, formset)
            messages.success(request, "Kainos atnaujintos")
            return redirect("detaliu_registras:uzklausa_detail", pk=uzklausa_pk)

        return render(
            request,
            self.template_name,
            {
                "formset": formset,
                "uzklausa": uzklausa,
            },
        )


class ImportCSVView(TemplateView):
    template_name = "detaliu_registras/import_csv.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ImportCSVForm()
        return context

    def post(self, request):
        form = ImportCSVForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                import_csv(form.cleaned_data["csv_file"])
                messages.success(request, "CSV failas sėkmingai importuotas")
                return redirect("admin:index")
            except Exception as e:
                logger.error(f"CSV import error: {e}")
                messages.error(request, "Klaida importuojant CSV failą")

        return render(request, self.template_name, {"form": form})


class KlientoUzklausosView(ListView):
    model = Uzklausa
    template_name = "detaliu_registras/kliento_uzklausos.html"
    context_object_name = "uzklausos"

    def get_queryset(self):
        klientas_id = self.kwargs["klientas_id"]
        return Uzklausa.objects.filter(klientas_id=klientas_id).select_related(
            "projektas", "detale"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        klientas_id = self.kwargs["klientas_id"]
        context["klientas"] = get_object_or_404(Klientas, pk=klientas_id)
        return context
