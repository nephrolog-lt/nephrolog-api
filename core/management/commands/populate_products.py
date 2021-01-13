import requests
from django.core.management.base import BaseCommand

from core.models import Product, ProductKind


class Command(BaseCommand):
    help = 'Populates products from DB'

    def handle(self, *args, **options):
        r = requests.get("https://foodbase.azurewebsites.net/Home/GetCategory")

        r.raise_for_status()

        for item in r.json():
            if item['EDIBLE'] is None or item['ENERKC'] == 0:
                continue

            defaults = {
                'name_lt': item['Name'],
                'name_en': item['NameEn'],
                'product_kind': ProductKind.Drink if item['EDIBLE'] > 0.9 else ProductKind.Food,
                'liquids_g': item['WATER'],
                'energy_kcal': item['ENERKC'],
                'potassium_mg': item['K'],
                'proteins_mg': item['PROT'] * 1000,
                'sodium_mg': item['NA'],
                'phosphorus_mg': item['P'],
            }

            Product.objects.update_or_create(
                    raw_id=item['Code'],
                    defaults=defaults
                )

