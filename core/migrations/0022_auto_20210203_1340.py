# Generated by Django 3.1.5 on 2021-02-03 13:40

from decimal import Decimal
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_intake_amount_ml'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicaluserprofile',
            name='weight_kg',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True, validators=[django.core.validators.MinValueValidator(Decimal('10'))]),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='weight_kg',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True, validators=[django.core.validators.MinValueValidator(Decimal('10'))]),
        ),
    ]
