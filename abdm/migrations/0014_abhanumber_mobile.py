# Generated by Django 4.2.10 on 2024-08-11 08:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("abdm", "0013_abhanumber_patient"),
    ]

    operations = [
        migrations.AddField(
            model_name="abhanumber",
            name="mobile",
            field=models.TextField(blank=True, null=True),
        ),
    ]