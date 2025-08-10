# detaliu_registras/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView, View
from django.contrib import messages
from django.db.models import Q
from .forms import (
    UzklausaCreationForm, DetaleForm, ProjektasForm,
    UzklausaFilterForm, KainaForm
)
from .models import Uzklausa, Klientas, Kaina
from .services import UzklausaService

class IndexView(TemplateView):
    template_name = 'detaliu_registras/index.html'

class UzklausaListView(ListView):
    model = Uzklausa
    template_name = 'detaliu_registras/uzklausa_list.html'
    context_object_name = 'uzklausos'
    paginate_by = 20

    def get_queryset(self):
        qs = (
            Uzklausa.objects
            .select_related('klientas', 'projektas', 'detale')
            .all()
        )
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(klientas__vardas__icontains=q) |
                Q(projektas__pavadinimas__icontains=q) |
                Q(detale__pavadinimas__icontains=q) |
                Q(detale__brezinio_nr__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter_form'] = UzklausaFilterForm(self.request.GET)
        return ctx

class UzklausaDetailView(DetailView):
    model = Uzklausa
    template_name = 'detaliu_registras/uzklausa_detail.html'
    context_object_name = 'uzklausa'

class UzklausaCreateView(View):
    template_name = 'detaliu_registras/uzklausa_create.html'

    def get(self, request):
        return render(request, self.template_name, {
            'form': UzklausaCreationForm(),
            'detale_form': DetaleForm(),
            'projektas_form': ProjektasForm(),
        })

    def post(self, request):
        form = UzklausaCreationForm(request.POST, request.FILES)
        if not form.is_valid():
            messages.error(request, 'Patikrinkite formos laukus.')
            return render(request, self.template_name, {
                'form': form,
                'detale_form': DetaleForm(request.POST, request.FILES),
                'projektas_form': ProjektasForm(request.POST),
            })

        uzklausa = UzklausaService.create_draft(form.cleaned_data, request.FILES)
        messages.success(request, 'Užklausos juodraštis sukurtas.')
        return redirect('detaliu_registras:uzklausa_detail', pk=uzklausa.pk)

class KainaUpdateView(View):
    template_name = 'detaliu_registras/kaina_update.html'

    def get(self, request, uzklausa_pk):
        uzklausa = get_object_or_404(Uzklausa, pk=uzklausa_pk)
        kaina = Kaina.objects.filter(detale=uzklausa.detale).first()
        form = KainaForm(instance=kaina) if kaina else KainaForm()
        return render(request, self.template_name, {'uzklausa': uzklausa, 'form': form})

    def post(self, request, uzklausa_pk):
        uzklausa = get_object_or_404(Uzklausa, pk=uzklausa_pk)
        kaina = Kaina.objects.filter(detale=uzklausa.detale).first()
        form = KainaForm(request.POST, instance=kaina)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.detale = uzklausa.detale
            obj.save()
            messages.success(request, 'Kaina išsaugota.')
            return redirect('detaliu_registras:uzklausa_detail', pk=uzklausa.pk)
        return render(request, self.template_name, {'uzklausa': uzklausa, 'form': form})

class KlientoUzklausosView(ListView):
    template_name = 'detaliu_registras/kliento_uzklausos.html'
    context_object_name = 'uzklausos'
    paginate_by = 20

    def get_queryset(self):
        klientas_id = self.kwargs.get('klientas_id')
        return (
            Uzklausa.objects
            .select_related('klientas', 'projektas', 'detale')
            .filter(klientas_id=klientas_id)
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['klientas'] = get_object_or_404(Klientas, id=self.kwargs.get('klientas_id'))
        return ctx

class ImportCSVView(TemplateView):
    template_name = 'detaliu_registras/import_csv.html'

    def post(self, request):
        messages.info(request, 'CSV importo logika bus suaktyvinta vėliau.')
        return redirect('detaliu_registras:index')
