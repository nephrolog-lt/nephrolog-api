import csv

import requests
from django.core.management.base import BaseCommand

from core.models import Product, ProductSource


class Command(BaseCommand):
    def handle(self, *args, **options):
        r = requests.get(
            "https://gist.githubusercontent.com/vycius/cb21d33a24394e3aa751b58cee6361b1/raw/1f55129d4d1705af1670c47b028b80241f4e8949/papildymas.csv")
        r.encoding = 'utf-8'
        r.raise_for_status()

        reader = csv.DictReader(r.iter_lines(decode_unicode='utf-8'))

        for item in reader:
            if not item['ID']:
                continue

            product = Product.objects.filter(raw_id=item['ID'], product_source=ProductSource.DN).first()

            if product is None or not item['Fat'] or not item['Carbohydrates']:
                continue

            product.fat_mg = float(item['Fat']) * 1000
            product.carbohydrates_mg = float(item['Carbohydrates']) * 1000

            if product.fat_mg < 0 or product.carbohydrates_mg < 0:
                print("Negative", item['ID'], item['Name'], item['Fat'], item['Carbohydrates'])
            else:
                product.save(update_fields=['fat_mg', 'carbohydrates_mg'])
