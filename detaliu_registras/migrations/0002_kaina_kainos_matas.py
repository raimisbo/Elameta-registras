# Generated by Django 5.0.7 on 2024-07-26 07:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('detaliu_registras', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='kaina',
            name='kainos_matas',
            field=models.CharField(choices=[('vnt.', 'vnt.'), ('kg', 'kg')], default='vnt.', max_length=10),
        ),
    ]
