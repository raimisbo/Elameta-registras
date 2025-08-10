"""
Service layer for business logic
Separates complex operations from views and models
"""

from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Klientas, Detale, Uzklausa
import logging

logger = logging.getLogger(__name__)


class UzklausaService:
    """Service for handling complex Uzklausa operations"""

    @staticmethod
    @transaction.atomic
    def create_full_request(form_data, projektas_form, detale_form, kaina_form):
        try:
            klientas = UzklausaService._get_or_create_klientas(form_data)

            projektas = projektas_form.save(commit=False)
            projektas.klientas = klientas
            projektas.save()

            detale = detale_form.save(commit=False)
            detale.projektas = projektas
            detale.save()
            detale_form.save_m2m()  # reikalinga ManyToMany laukui "danga"

            kaina = kaina_form.save(commit=False)
            kaina.detalė = detale
            kaina.busena = "aktuali"
            kaina.save()

            uzklausa = Uzklausa.objects.create(
                klientas=klientas,
                projektas=projektas,
                detale=detale,
            )

            return uzklausa

        except Exception as e:
            logger.error(f"Klaida kuriant užklausą: {e}")
            raise ValidationError([f"Nepavyko sukurti užklausos: {e}"])

    @staticmethod
    def _get_or_create_klientas(form_data):
        """Handle client selection or creation"""
        existing_klientas = form_data.get("existing_klientas")
        new_klientas_vardas = form_data.get("new_klientas_vardas")

        if existing_klientas:
            return existing_klientas
        elif new_klientas_vardas:
            return Klientas.objects.create(
                vardas=new_klientas_vardas,
                # Add other required fields with defaults
                telefonas="",  # This should be required in form
            )
        else:
            raise ValidationError("Klientas privalomas")

    @staticmethod
    @transaction.atomic
    def update_prices(detale, formset):
        """
        Update all prices for a detail
        Handles complex price versioning logic
        """
        try:
            # Mark old prices as 'sena'
            detale.kainos.filter(busena="aktuali").update(busena="sena")

            # Create new prices
            for form in formset:
                if form.cleaned_data and not form.cleaned_data.get("DELETE"):
                    kaina = form.save(commit=False)
                    kaina.detale = detale
                    kaina.busena = "aktuali"  # New prices are always active
                    kaina.save()

            logger.info(f"Updated prices for detail {detale.pavadinimas}")

        except Exception as e:
            logger.error(f"Error updating prices: {e}")
            raise ValidationError(f"Nepavyko atnaujinti kainų: {e}")

    @staticmethod
    def get_active_price(detale, quantity):
        """
        Get the active price for a detail based on quantity
        Business logic for price calculation
        """
        active_prices = detale.kainos.filter(busena="aktuali")

        # Find price that matches quantity range
        for price in active_prices:
            if price.yra_fiksuota:
                if quantity == price.fiksuotas_kiekis:
                    return price
            else:
                if (
                    (price.kiekis_nuo or 0)
                    <= quantity
                    <= (price.kiekis_iki or float("inf"))
                ):
                    return price

        return None


class ReportService:
    """Service for generating reports and analytics"""

    @staticmethod
    def get_client_statistics():
        """Get statistics about clients and their requests"""
        from django.db.models import Count

        stats = Klientas.objects.annotate(
            uzklausu_kiekis=Count("uzklausa"),
            projektu_kiekis=Count("projektas", distinct=True),
        ).values("vardas", "uzklausu_kiekis", "projektu_kiekis")

        return list(stats)

    @staticmethod
    def get_coating_usage_stats():
        """Get statistics about coating types usage"""
        from django.db.models import Count

        # This would need proper Many-to-Many handling
        coating_stats = (
            Detale.objects.values("danga__pavadinimas")
            .annotate(usage_count=Count("id"))
            .order_by("-usage_count")
        )

        return list(coating_stats)


class ValidationService:
    """Service for complex validation logic"""

    @staticmethod
    def validate_price_ranges(prices_data):
        """Validate that price ranges don't overlap"""
        sorted_prices = sorted(prices_data, key=lambda x: x.get("kiekis_nuo", 0))

        for i in range(len(sorted_prices) - 1):
            current = sorted_prices[i]
            next_price = sorted_prices[i + 1]

            current_end = current.get("kiekis_iki")
            next_start = next_price.get("kiekis_nuo")

            if current_end and next_start and current_end >= next_start:
                raise ValidationError(
                    f"Kainų diapazonai persidengia: {current_end} >= {next_start}"
                )

        return True

    @staticmethod
    def validate_project_dates(uzklausos_data, pasiulymo_data):
        """Validate project dates make business sense"""
        if uzklausos_data > pasiulymo_data:
            raise ValidationError(
                "Pasiūlymo data negali būti ankstesnė už užklausos datą"
            )

        return True
