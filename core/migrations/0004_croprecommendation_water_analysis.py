# Generated by Django 5.1.2 on 2024-12-17 18:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_croprecommendation_recommendedcrop"),
    ]

    operations = [
        migrations.AddField(
            model_name="croprecommendation",
            name="water_analysis",
            field=models.TextField(null=True),
        ),
    ]