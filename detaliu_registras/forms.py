from django import forms
from .models import Klientas, Projektas, Detale, Kaina, Uzklausa, Danga

class ImportCSVForm(forms.Form):
    csv_file = forms.FileField(label="CSV failas")

class UzklausaFilterForm(forms.Form):
    q = forms.CharField(
        required=False, 
        label='Ieškoti', 
        widget=forms.TextInput(attrs={'placeholder': 'Ieškoti...'})
    )

# Separate forms for each model - proper architecture
class KlientasForm(forms.ModelForm):
    class Meta:
        model = Klientas
        fields = ['vardas', 'adresas', 'telefonas', 'email']
        widgets = {
            'email': forms.EmailInput(),
        }

class ProjektasForm(forms.ModelForm):
    class Meta:
        model = Projektas
        fields = ['klientas', 'pavadinimas', 'uzklausos_data', 'pasiulymo_data']
        widgets = {
            'uzklausos_data': forms.DateInput(attrs={'type': 'date'}),
            'pasiulymo_data': forms.DateInput(attrs={'type': 'date'}),
        }

class DetaleForm(forms.ModelForm):
    danga = forms.ModelMultipleChoiceField(
        queryset=Danga.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Danga"
    )

    class Meta:
        model = Detale
        fields = [
            'pavadinimas', 'brezinio_nr', 'plotas', 'svoris',
            'kiekis_metinis', 'kiekis_menesis', 'kiekis_partijai',
            'ppap_dokumentai', 'danga', 'standartas', 'kabinimo_tipas',
            'kabinimas_xyz', 'kiekis_reme', 'faktinis_kiekis_reme',
            'pakavimas', 'nuoroda_brezinio', 'nuoroda_pasiulymo', 'pastabos'
        ]
        widgets = {
            'ppap_dokumentai': forms.Textarea(attrs={'rows': 3}),
            'pastabos': forms.Textarea(attrs={'rows': 3}),
            'faktinis_kiekis_reme': forms.NumberInput(attrs={'value': 0}),
        }

class KainaForm(forms.ModelForm):
    class Meta:
        model = Kaina
        fields = ['busena', 'suma', 'yra_fiksuota', 'kiekis_nuo', 'kiekis_iki', 
                 'fiksuotas_kiekis', 'kainos_matas']
        widgets = {
            'kiekis_nuo': forms.NumberInput(attrs={'min': 0}),
            'kiekis_iki': forms.NumberInput(attrs={'min': 0}),
            'fiksuotas_kiekis': forms.NumberInput(attrs={'value': 100, 'min': 0}),
        }

    def clean(self):
        cleaned_data = super().clean()
        kiekis_nuo = cleaned_data.get('kiekis_nuo')
        kiekis_iki = cleaned_data.get('kiekis_iki')
        
        if kiekis_nuo and kiekis_iki and kiekis_nuo >= kiekis_iki:
            raise forms.ValidationError("Kiekis 'nuo' turi būti mažesnis nei 'iki'")
        
        return cleaned_data

# Composite form for complex creation workflow
class UzklausaCreationForm(forms.Form):
    existing_klientas = forms.ModelChoiceField(
        queryset=Klientas.objects.all(),
        required=False,
        label="Pasirinkti esamą klientą"
    )
    new_klientas_vardas = forms.CharField(
        max_length=100,
        required=False,
        label="Arba įvesti naują klientą"
    )

    def clean(self):
        cleaned_data = super().clean()
        existing = cleaned_data.get("existing_klientas")
        new = cleaned_data.get("new_klientas_vardas")

        if not existing and not new:
            raise forms.ValidationError("Pasirinkite arba įveskite klientą.")
        if existing and new:
            raise forms.ValidationError("Pasirinkite tik vieną variantą.")

        return cleaned_data