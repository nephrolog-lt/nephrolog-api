import csv
from pprint import pprint

import requests
from django.core.management.base import BaseCommand

from core.models import Product, ProductKind, ProductSource, ProductRegion


class Command(BaseCommand):
    help = 'Populates products from Danish DB'

    def handle(self, *args, **options):
        r = requests.get(
            "https://gist.githubusercontent.com/vycius/6cb2b1148efcaa2d6d48b91e1169770e/raw/f2abc201a842d4c2594116b6f11caf1b05044b74/swiss.csv")
        r.encoding = 'utf-8'
        r.raise_for_status()

        reader = csv.DictReader(r.iter_lines(decode_unicode='utf-8'))

        for item in reader:
            kind = ProductKind.Drink if item['Matrix unit'] == 'pro 100 ml' else ProductKind.Food
            density = float(item['Density']) if kind == ProductKind.Drink else None
            multiplicator = density or 1

            try:
                defaults = {
                    'name': item['Name'],
                    'name_en': item['name_en'],
                    'synonyms': item['Synonyms'],
                    'product_kind': kind,
                    'density_g_ml': density,
                    'region': ProductRegion.DE,
                    'potassium_mg': round(float(item['Potassium (K) (mg)']) * multiplicator),
                    'proteins_mg': round(float(item['Protein (g)']) * 1000.0 * multiplicator),
                    'sodium_mg': round(float(item['Sodium (Na) (mg)']) * multiplicator),
                    'liquids_g': round(float(item['Water (g)']) * multiplicator),
                    'energy_kcal': round(float(item['Energy, kilocalories (kcal)']) * multiplicator),
                    'phosphorus_mg': round(float(item['Phosphorus (P) (mg)']) * multiplicator),
                    'carbohydrates_mg': round(float(item['Carbohydrates, available (g)']) * 1000.0 * multiplicator),
                    'fat_mg': round(float(item['Fat, total (g)']) * 1000.0 * multiplicator),
                }
            except:
                continue


            Product.objects.update_or_create(
                raw_id=item['ID'],
                product_source=ProductSource.SW,
                defaults=defaults
            )
