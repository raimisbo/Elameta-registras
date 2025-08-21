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


# Failas: detaliu_registras/views.py
# PASTABA: čia pateikiama tik UzklausaListView pilna klasė.
# -> Įdėk/PAKEISK šią klasę savo views.py faile (kitų klasių ir importų neliesti).
# -> Jei trūksta importų, pridėk juos viršuje (žr. sąrašą žemiau).



class UzklausaListView(ListView):
    """
    Sąrašas su per-stulpeliniais filtrais (server-side) ir puslapiavimu.
    JS pusėje — tik stulpelių rodymo/slėpimo logika ir auto-submit filtrams.
    """
    model = Uzklausa
    template_name = "detaliu_registras/uzklausa_list.html"
    context_object_name = "uzklausos"
    paginate_by = 20

    def get_queryset(self):
        qs = (
            Uzklausa.objects
            .select_related("klientas", "projektas", "detale")
            .all()
        )
        g = self.request.GET

        v = g.get("f_klientas")
        if v: qs = qs.filter(klientas__vardas__icontains=v)

        v = g.get("f_projektas")
        if v: qs = qs.filter(projektas__pavadinimas__icontains=v)

        v = g.get("f_uzklausos_data_from")
        if v: qs = qs.filter(projektas__uzklausos_data__gte=v)
        v = g.get("f_uzklausos_data_to")
        if v: qs = qs.filter(projektas__uzklausos_data__lte=v)

        v = g.get("f_pasiulymo_data_from")
        if v: qs = qs.filter(projektas__pasiulymo_data__gte=v)
        v = g.get("f_pasiulymo_data_to")
        if v: qs = qs.filter(projektas__pasiulymo_data__lte=v)

        v = g.get("f_detale")
        if v: qs = qs.filter(detale__pavadinimas__icontains=v)

        v = g.get("f_brezinio_nr")
        if v: qs = qs.filter(detale__brezinio_nr__icontains=v)

        v = g.get("f_kiekis_min")
        if v: qs = qs.filter(detale__kiekis_menesis__gte=v)
        v = g.get("f_kiekis_max")
        if v: qs = qs.filter(detale__kiekis_menesis__lte=v)

        return qs


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

class DetaliuTableView(TemplateView):
    template_name = "detaliu_registras/detaliu_list.html"