import csv

import requests
from django.core.management.base import BaseCommand

from core.models import Product, ProductKind, ProductSource


class Command(BaseCommand):
    help = 'Populates products from Danish DB'

    def handle(self, *args, **options):
        r = requests.get(
            "https://gist.githubusercontent.com/vycius/d79fffd86153c8e11c779ea60bea684a/raw/68d72831fdabcd44ff6da82429c07784bd6f3af2/nutrients.csv")
        r.encoding = 'utf-8'
        r.raise_for_status()

        reader = csv.DictReader(r.iter_lines(decode_unicode='utf-8'))

        for item in reader:
            defaults = {
                'name_lt': item['LT'],
                'name_en': item['EN'],
                'product_kind': ProductKind.Food,
                'liquids_g': round(float(item['Water'])),
                'energy_kcal': round(float(item['Energy'])),
                'potassium_mg': item['Potassium'],
                'proteins_mg': round(float(item['Protein'])),
                'sodium_mg': item['Sodium'],
                'phosphorus_mg': item['Phosphorus'],
            }

            Product.objects.update_or_create(
                raw_id=item['Id'],
                product_source=ProductSource.DN,
                defaults=defaults
            )
