from datetime import date

from django.test import TestCase

from core.models import DailyIntakesReport, UserProfile
from core.tests.factories import DailyIntakesReportFactory, IntakeFactory, ProductFactory, UserFactory, \
    UserProfileFactory


class UserProfileTests(TestCase):

    def test_age_calculation(self):
        user = UserFactory()
        UserProfileFactory(user=user, year_of_birth=1960)
        expected_age = (date.today().year - 1960)

        queryset = UserProfile.objects.annotate_with_age()

        self.assertAlmostEqual(queryset.first().age, expected_age, delta=1)


class IntakeTests(TestCase):

    def test_annotating_with_total_norms(self):
        user = UserFactory()

        product1 = ProductFactory(
            potassium_mg=10,
            sodium_mg=20,
            phosphorus_mg=30,
            proteins_mg=40,
            energy_kcal=50,
            liquids_g=60,
        )
        product2 = ProductFactory(
            potassium_mg=15,
            sodium_mg=25,
            phosphorus_mg=35,
            proteins_mg=32767,
            energy_kcal=32767,
            liquids_g=32767,
        )
        daily_report = DailyIntakesReportFactory(user=user)

        IntakeFactory(user=user, daily_report=daily_report, product=product1, amount_g=100)
        IntakeFactory(user=user, daily_report=daily_report, product=product2, amount_g=200)

        annotated_daily_report = DailyIntakesReport.objects.annotate_with_nutrient_totals().first()

        self.assertEqual(annotated_daily_report.total_potassium_mg, 40)
        self.assertEqual(annotated_daily_report.total_sodium_mg, 70)
        self.assertEqual(annotated_daily_report.total_phosphorus_mg, 100)
        self.assertEqual(annotated_daily_report.total_proteins_mg, 65574)
        self.assertEqual(annotated_daily_report.total_energy_kcal, 65584)
        self.assertEqual(annotated_daily_report.total_liquids_g, 65594)
