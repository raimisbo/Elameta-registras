from django.db.models import OuterRef, Subquery, F
from django.db.models.functions import Coalesce
from rest_framework import serializers, viewsets
from rest_framework_datatables.renderers import DatatablesRenderer
from rest_framework_datatables.pagination import DatatablesPageNumberPagination
from rest_framework_datatables.filters import DatatablesFilterBackend
from .models import Detale, Kaina

class DetaleListSerializer(serializers.ModelSerializer):
    kliento_pavadinimas = serializers.CharField(read_only=True)
    projekto_pavadinimas = serializers.CharField(read_only=True)
    detales_pavadinimas = serializers.CharField(read_only=True)
    uzklausos_data = serializers.DateField(read_only=True)
    pasiulymo_data = serializers.DateField(read_only=True)
    kainos_busena = serializers.CharField(read_only=True, allow_null=True)
    detales_kainos_suma = serializers.FloatField(read_only=True, allow_null=True)
    kainos_fiksuotas_kiekis = serializers.IntegerField(read_only=True, allow_null=True)
    kainos_matas = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = Detale
        fields = [
            "id","kliento_pavadinimas","projekto_pavadinimas","detales_pavadinimas",
            "uzklausos_data","pasiulymo_data","brezinio_nr","kainos_busena",
            "detales_kainos_suma","kainos_fiksuotas_kiekis","kainos_matas",
            "kiekis_reme","pastabos",
        ]

class DetaleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DetaleListSerializer
    renderer_classes = (DatatablesRenderer,)
    pagination_class = DatatablesPageNumberPagination
    filter_backends = (DatatablesFilterBackend,)
    http_method_names = ["get","head","options"]

    def get_queryset(self):
        kaina_akt = Kaina.objects.filter(detalė_id=OuterRef("pk"), busena="aktuali").order_by("-id")
        kaina_any = Kaina.objects.filter(detalė_id=OuterRef("pk")).order_by("-id")
        return (
            Detale.objects.select_related("projektas","projektas__klientas")
            .annotate(
                kliento_pavadinimas=F("projektas__klientas__vardas"),
                projekto_pavadinimas=F("projektas__pavadinimas"),
                detales_pavadinimas=F("pavadinimas"),
                uzklausos_data=F("projektas__uzklausos_data"),
                pasiulymo_data=F("projektas__pasiulymo_data"),
                kainos_busena=Coalesce(Subquery(kaina_akt.values("busena")[:1]),
                                       Subquery(kaina_any.values("busena")[:1])),
                detales_kainos_suma=Coalesce(Subquery(kaina_akt.values("suma")[:1]),
                                             Subquery(kaina_any.values("suma")[:1])),
                kainos_fiksuotas_kiekis=Coalesce(Subquery(kaina_akt.values("fiksuotas_kiekis")[:1]),
                                                 Subquery(kaina_any.values("fiksuotas_kiekis")[:1])),
                kainos_matas=Coalesce(Subquery(kaina_akt.values("kainos_matas")[:1]),
                                      Subquery(kaina_any.values("kainos_matas")[:1])),
            )
        )
