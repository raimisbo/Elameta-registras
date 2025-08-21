# Failas: detaliu_registras/views_ajax.py
# Paskirtis: AJAX daliniai vaizdai (be layout'o) – "Detaliau" užklausų sąraše.

from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from django.views.decorators.http import require_GET

# ⚠️ Jei tavo modelis vadinasi kitaip nei Uzklausa – pakeisk importą.
from .models import Uzklausa


@require_GET
def uzklausa_details(request, pk: int):
    """
    Grąžina HTML <tr class="row-details"> su išplėsta informacija apie konkrečią užklausą.
    Skirta dinamiškai įterpti po sąrašo eilute (be pilno puslapio perkrovimo).
    """
    # 1) Saugus paėmimas – 404 vietoje 500, jei neegzistuoja
    obj = get_object_or_404(Uzklausa, pk=pk)

    # 2) Bandome sugeneruoti dalinį šabloną; jeigu šablono nėra – grąžinam gražų <tr> su klaidos žinute.
    try:
        html = render_to_string(
            "detaliu_registras/_uzklausa_details.html",
            {"uzklausa": obj},
            request=request,
        )
    except TemplateDoesNotExist:
        html = (
            '<tr class="row-details">'
            '<td colspan="100">'
            '<div class="rd-error">Šablonas <code>detaliu_registras/_uzklausa_details.html</code> nerastas.</div>'
            '</td>'
            '</tr>'
        )

    # 3) Sėkmės atveju (ar net ir su klaidos žinute) grąžinam 200 su <tr>, kad JS galėtų įterpti į DOM.
    return HttpResponse(html)
