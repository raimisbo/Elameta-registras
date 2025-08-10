# detaliu_registras/services.py
from django.db import transaction
from .models import Klientas, Projektas, Detale, Uzklausa, Kaina, Danga

class UzklausaService:
    @staticmethod
    @transaction.atomic
    def create_draft(data, files=None):
        """
        Sukuria Uzklausa juodraštį iš formos laukų, leidžiant daug tuščių reikšmių.
        data – request.POST (ar suformuotas dict), files – request.FILES
        """
        files = files or {}

        # 1) Klientas: esamas arba naujas
        klientas = data.get('existing_klientas')
        if klientas:
            if not isinstance(klientas, Klientas):
                klientas = Klientas.objects.filter(pk=klientas).first()
        if not klientas:
            klientas = Klientas.objects.create(
                vardas=(data.get('new_klientas_vardas') or '').strip() or 'Be pavadinimo',
                adresas=(data.get('new_klientas_adresas') or '').strip() or None,
                telefonas=(data.get('new_klientas_telefonas') or '').strip() or None,
                email=(data.get('new_klientas_email') or '').strip() or ''
            )

        # 2) Projektas (gali būti su tuščiais datų laukais)
        projektas = Projektas.objects.create(
            klientas=klientas,
            pavadinimas=(data.get('projektas_pavadinimas') or '').strip() or 'Be pavadinimo',
            uzklausos_data=(data.get('uzklausos_data') or None),
            pasiulymo_data=(data.get('pasiulymo_data') or None),
        )

        # 3) Detalė (leidžiam tuščius)
        danga_obj = None
        danga_id = data.get('detale_danga')
        if danga_id:
            danga_obj = Danga.objects.filter(pk=danga_id).first()

        detale = Detale.objects.create(
            pavadinimas=(data.get('detale_pavadinimas') or '').strip() or 'Be pavadinimo',
            brezinio_nr=(data.get('detale_brezinio_nr') or '').strip() or '',
            nuotrauka=files.get('detale_nuotrauka'),
            nuoroda_pasiulymo=(data.get('detale_nuoroda_pasiulymo') or '').strip() or '',
            pastabos=(data.get('detale_pastabos') or '').strip() or '',
            kiekis_menesis=(data.get('detale_kiekis_menesis') or None),
            danga=danga_obj
        )

        # 4) Užklausa – sujungia viską
        uzklausa = Uzklausa.objects.create(
            klientas=klientas,
            projektas=projektas,
            detale=detale
        )

        return uzklausa
