from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.db.models import Q, Count
from django.contrib import messages
from django.urls import reverse_lazy
from django.forms import formset_factory
import json
import logging

from .models import Klientas, Detale, Uzklausa, Projektas, Kaina
from .forms import (
    ImportCSVForm, UzklausaCreationForm, KainaForm, 
    UzklausaFilterForm, DetaleForm, ProjektasForm
)
from .services import UzklausaService  # We'll create this
from .utils import import_csv

logger = logging.getLogger(__name__)

class IndexView(TemplateView):
    """Dashboard view with client statistics"""
    template_name = 'index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get client statistics
        klientu_duomenys = Uzklausa.objects.values(
            'klientas__vardas', 'klientas__id'
        ).annotate(kiekis=Count('id'))
        
        context.update({
            'uzklausos': Uzklausa.objects.all()[:10],  # Latest 10
            'klientu_duomenys_json': json.dumps(list(klientu_duomenys)),
        })
        return context

class UzklausaListView(ListView):
    """List all requests with filtering"""
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
    """View single request details"""
    model = Uzklausa
    template_name = 'detaliu_registras/uzklausa_detail.html'
    context_object_name = 'uzklausa'
    
    def get_queryset(self):
        return Uzklausa.objects.select_related(
            'klientas', 'projektas', 'detale'
        ).prefetch_related('detale__kainos')

class UzklausaCreateView(TemplateView):
    """Create new request using service layer"""
    template_name = 'detaliu_registras/uzklausa_create.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = UzklausaCreationForm()
        return context
    
    def post(self, request):
        form = UzklausaCreationForm(request.POST)
        if form.is_valid():
            try:
                # Use service layer for complex creation logic
                uzklausa = UzklausaService.create_full_request(form.cleaned_data)
                messages.success(self.request, 'Užklausa sėkmingai sukurta')
                return redirect('detaliu_registras:uzklausa_detail', pk=uzklausa.pk)
            except Exception as e:
                logger.error(f"Error creating request: {e}")
                messages.error(self.request, 'Klaida kuriant užklausą')
        
        return render(request, self.template_name, {'form': form})

class KainaUpdateView(UpdateView):
    """Update prices for a detail using formsets"""
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
            # Use service layer for price updates
            UzklausaService.update_prices(uzklausa.detale, formset)
            messages.success(request, 'Kainos atnaujintos')
            return redirect('detaliu_registras:uzklausa_detail', pk=uzklausa_pk)
        
        return render(request, self.template_name, {
            'formset': formset,
            'uzklausa': uzklausa,
        })

class ImportCSVView(TemplateView):
    """Import data from CSV"""
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
    """List requests for specific client"""
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