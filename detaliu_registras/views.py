from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Q, Count
from django.contrib import messages
from django.urls import reverse_lazy
from django.forms import formset_factory
from django.core.exceptions import ValidationError
import json
import logging

from .models import Klientas, Detale, Uzklausa, Projektas, Kaina
from .forms import (
    ImportCSVForm, UzklausaCreationForm, KainaForm,
    UzklausaFilterForm, DetaleForm, ProjektasForm
)
from .services import UzklausaService
from .utils import import_csv

logger = logging.getLogger(__name__)


class IndexView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        klientu_duomenys = Uzklausa.objects.values(
            'klientas__vardas', 'klientas__id'
        ).annotate(kiekis=Count('id'))

        context.update({
            'uzklausos': Uzklausa.objects.all()[:10],
            'klientu_duomenys_json': json.dumps(list(klientu_duomenys)),
        })
        return context


class UzklausaListView(ListView):
    model = Uzklausa
    template_name = 'detaliu_registras/uzklausa_list.html'
    context_object_name = 'uzklausos'
    paginate_by = 20

    def get_queryset(self):
        queryset = Uzklausa.objects.select_related(
            'klientas', 'projektas', 'detale'
        ).all()

        query = self.request.GET.get('q', '')
        if query:
            queryset = queryset.filter(
                Q(klientas__vardas__icontains=query) |
                Q(projektas__pavadinimas__icontains=query) |
                Q(detale__pavadinimas__icontains=query) |
                Q(detale__brezinio_nr__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = UzklausaFilterForm(self.request.GET)
        return context


class UzklausaDetailView(DetailView):
    model = Uzklausa
    template_name = 'detaliu_registras/uzklausa_detail.html'
    context_object_name = 'uzklausa'

    def get_queryset(self):
        return Uzklausa.objects.select_related(
            'klientas', 'projektas', 'detale'
        ).prefetch_related('detale__kainos')


class UzklausaCreateView(TemplateView):
    template_name = 'detaliu_registras/uzklausa_create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = UzklausaCreationForm()
        context['projektas_form'] = ProjektasForm()
        context['detale_form'] = DetaleForm()
        context['kaina_form'] = KainaForm()
        return context

    def post(self, request):
        form = UzklausaCreationForm(request.POST)
        projektas_form = ProjektasForm(request.POST)
        detale_form = DetaleForm(request.POST)
        kaina_form = KainaForm(request.POST)

        if all([form.is_valid(), projektas_form.is_valid(), detale_form.is_valid(), kaina_form.is_valid()]):
            try:
                uzklausa = UzklausaService.create_full_request(
                    form.cleaned_data,
                    projektas_form,
                    detale_form,
                    kaina_form
                )
                messages.success(request, 'Užklausa sėkmingai sukurta')
                return redirect('detaliu_registras:uzklausa_detail', pk=uzklausa.pk)
            except ValidationError as e:
                messages.error(request, f"Klaida: {e}")
        else:
            messages.error(request, "Formoje yra klaidų – patikrinkite visus laukus.")

        return render(request, self.template_name, {
            'form': form,
            'projektas_form': projektas_form,
            'detale_form': detale_form,
            'kaina_form': kaina_form,
        })


class KainaUpdateView(TemplateView):
    template_name = 'detaliu_registras/kaina_update.html'

    def get(self, request, uzklausa_pk):
        uzklausa = get_object_or_404(Uzklausa, pk=uzklausa_pk)
        KainaFormSet = formset_factory(KainaForm, extra=1, can_delete=True)

        initial_data = [
            {
                'busena': k.busena,
                'suma': k.suma,
                'kiekis_nuo': k.kiekis_nuo,
                'kiekis_iki': k.kiekis_iki,
                'fiksuotas_kiekis': k.fiksuotas_kiekis,
                'kainos_matas': k.kainos_matas
            }
            for k in uzklausa.detale.kainos.all()
        ]

        formset = KainaFormSet(initial=initial_data)

        return render(request, self.template_name, {
            'formset': formset,
            'uzklausa': uzklausa,
        })

    def post(self, request, uzklausa_pk):
        uzklausa = get_object_or_404(Uzklausa, pk=uzklausa_pk)
        KainaFormSet = formset_factory(KainaForm, extra=1, can_delete=True)
        formset = KainaFormSet(request.POST)

        if formset.is_valid():
            UzklausaService.update_prices(uzklausa.detale, formset)
            messages.success(request, 'Kainos atnaujintos')
            return redirect('detaliu_registras:uzklausa_detail', pk=uzklausa_pk)

        return render(request, self.template_name, {
            'formset': formset,
            'uzklausa': uzklausa,
        })


class ImportCSVView(TemplateView):
    template_name = 'detaliu_registras/import_csv.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ImportCSVForm()
        return context

    def post(self, request):
        form = ImportCSVForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                import_csv(form.cleaned_data['csv_file'])
                messages.success(request, 'CSV failas sėkmingai importuotas')
                return redirect('admin:index')
            except Exception as e:
                logger.error(f"CSV import error: {e}")
                messages.error(request, 'Klaida importuojant CSV failą')

        return render(request, self.template_name, {'form': form})


class KlientoUzklausosView(ListView):
    model = Uzklausa
    template_name = 'detaliu_registras/kliento_uzklausos.html'
    context_object_name = 'uzklausos'

    def get_queryset(self):
        klientas_id = self.kwargs['klientas_id']
        return Uzklausa.objects.filter(
            klientas_id=klientas_id
        ).select_related('projektas', 'detale')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        klientas_id = self.kwargs['klientas_id']
        context['klientas'] = get_object_or_404(Klientas, pk=klientas_id)
        return context
