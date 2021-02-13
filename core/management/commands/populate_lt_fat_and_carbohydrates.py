import requests
from django.core.management.base import BaseCommand

from core.models import Product, ProductSource


class Command(BaseCommand):
    help = 'Populates products from DB'

    def handle(self, *args, **options):
        r = requests.get("https://foodbase.azurewebsites.net/Home/GetCategory")

        # FAT
        r.raise_for_status()

        for item in r.json():
            if not item['Code']:
                continue

            product = Product.objects.filter(raw_id=item['Code'], product_source=ProductSource.LT).first()

            if product is None:
                continue

            product.fat_mg = item['FAT'] * 1000
            product.carbohydrates_mg = item['CHO'] * 1000

            product.save(update_fields=['fat_mg', 'carbohydrates_mg'])
