from django import forms
from .models import Klientas, Projektas, Detale, Kaina

class UzklausaCreationForm(forms.Form):
    # Esamas klientas
    existing_klientas = forms.ModelChoiceField(
        queryset=Klientas.objects.all(),
        required=False,
        label='Esamas klientas'
    )

    # Naujo kliento laukai
    new_klientas_vardas = forms.CharField(required=False, label='Naujo kliento vardas')
    new_klientas_adresas = forms.CharField(required=False, label='Adresas')
    new_klientas_telefonas = forms.CharField(required=False, label='Telefonas')
    new_klientas_email = forms.EmailField(required=False, label='El. paštas')

    # Projekto laukai
    projektas_pavadinimas = forms.CharField(required=False, label='Projekto pavadinimas')
    uzklausos_data = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    pasiulymo_data = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    # Detalės laukai
    detale_pavadinimas = forms.CharField(required=False, label='Detalės pavadinimas')
    detale_brezinio_nr = forms.CharField(required=False, label='Brezinio Nr.')
    detale_nuotrauka = forms.ImageField(required=False, label='Nuotrauka')
    detale_nuoroda_pasiulymo = forms.URLField(required=False, label='Nuoroda į pasiūlymą')
    detale_pastabos = forms.CharField(required=False, widget=forms.Textarea, label='Pastabos')
    detale_kiekis_menesis = forms.IntegerField(required=False, label='Kiekis per mėnesį')
    detale_danga = forms.IntegerField(required=False, label='Dangos ID')  # Bus paversta į objektą services sluoksnyje


class ProjektasForm(forms.ModelForm):
    class Meta:
        model = Projektas
        fields = ['pavadinimas', 'uzklausos_data', 'pasiulymo_data']
        widgets = {
            'uzklausos_data': forms.DateInput(attrs={'type': 'date'}),
            'pasiulymo_data': forms.DateInput(attrs={'type': 'date'}),
        }


class DetaleForm(forms.ModelForm):
    class Meta:
        model = Detale
        fields = [
            'pavadinimas', 'brezinio_nr', 'nuotrauka', 'nuoroda_pasiulymo',
            'pastabos', 'kiekis_menesis', 'danga'
        ]


class KainaForm(forms.ModelForm):
    class Meta:
        model = Kaina
        fields = ['kaina_nuo', 'kaina_iki', 'suma', 'kainos_matas']


class UzklausaFilterForm(forms.Form):
    q = forms.CharField(required=False, label='Paieška')
