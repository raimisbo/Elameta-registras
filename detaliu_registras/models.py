# detaliu_registras/models.py
from django.db import models

class Klientas(models.Model):
    vardas = models.CharField(max_length=100)
    adresas = models.CharField(max_length=255, blank=True, null=True)
    telefonas = models.CharField(max_length=20, blank=True, null=True)
    email = models.TextField(default='', blank=True)

    def __str__(self):
        return self.vardas

class Projektas(models.Model):
    klientas = models.ForeignKey(Klientas, on_delete=models.CASCADE)
    pavadinimas = models.CharField(max_length=100)
    uzklausos_data = models.DateField(blank=True, null=True)
    pasiulymo_data = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.pavadinimas

class Danga(models.Model):
    pavadinimas = models.CharField(max_length=100)

    def __str__(self):
        return self.pavadinimas

class Detale(models.Model):
    pavadinimas = models.CharField(max_length=100)
    brezinio_nr = models.CharField(max_length=100, blank=True, default='')
    nuotrauka = models.ImageField(upload_to='detales/', blank=True, null=True)
    nuoroda_pasiulymo = models.URLField(blank=True, default='')
    pastabos = models.TextField(blank=True, default='')
    kiekis_menesis = models.IntegerField(blank=True, null=True)
    danga = models.ForeignKey(Danga, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.pavadinimas

class Kaina(models.Model):
    detale = models.ForeignKey(Detale, on_delete=models.CASCADE)
    kaina_nuo = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    kaina_iki = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    suma = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    kainos_matas = models.CharField(max_length=50, blank=True, default='')

    def __str__(self):
        return f"Kaina: {self.kaina_nuo} - {self.kaina_iki}"

class Uzklausa(models.Model):
    klientas = models.ForeignKey(Klientas, on_delete=models.CASCADE)
    projektas = models.ForeignKey(Projektas, on_delete=models.CASCADE)
    detale = models.ForeignKey(Detale, on_delete=models.CASCADE)

    def __str__(self):
        return f"Užklausa {self.pk}"
