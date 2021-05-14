import csv
import sys

from django.core.management.base import BaseCommand
from django.db.models.aggregates import Count

from core.models import DailyIntakesReport


class Command(BaseCommand):

    def handle(self, *args, **options):
        reports = DailyIntakesReport.objects.annotate(
            intakes_count=Count('intakes')
        ).annotate_with_nutrient_totals().select_related('user')

        fieldnames = [
            'user_id', 'intakes_count', 'date',
            'daily_norm_potassium_mg', 'total_potassium_mg',
            'daily_norm_proteins_mg', 'total_proteins_mg',
            'daily_norm_sodium_mg', 'total_sodium_mg',
            'daily_norm_phosphorus_mg', 'total_phosphorus_mg',
            'daily_norm_energy_kcal', 'total_energy_kcal',
            'daily_norm_liquids_g', 'total_liquids_g',
            'created_at', 'updated_at',
        ]
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)

        writer.writeheader()
        for report in reports:
            writer.writerow({
                'user_id': report.user.id,
                'intakes_count': report.intakes_count,
                'date': report.date,
                'daily_norm_potassium_mg': report.daily_norm_potassium_mg,
                'total_potassium_mg': report.total_potassium_mg,
                'daily_norm_proteins_mg': report.daily_norm_proteins_mg,
                'total_proteins_mg': report.total_proteins_mg,
                'daily_norm_sodium_mg': report.daily_norm_sodium_mg,
                'total_sodium_mg': report.total_sodium_mg,
                'daily_norm_phosphorus_mg': report.daily_norm_phosphorus_mg,
                'total_phosphorus_mg': report.total_phosphorus_mg,
                'daily_norm_energy_kcal': report.daily_norm_energy_kcal,
                'total_energy_kcal': report.total_energy_kcal,
                'daily_norm_liquids_g': report.daily_norm_liquids_g,
                'total_liquids_ml': report.total_liquids_ml,
                'created_at': report.created_at,
                'updated_at': report.updated_at,
            })
