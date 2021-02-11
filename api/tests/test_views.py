from datetime import date, datetime, timedelta

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory, APITestCase

from core.models import User
from core.tests.factories import DailyIntakesReportFactory, IntakeFactory, ProductFactory, UserFactory, \
    UserProfileFactory


class BaseApiText(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user('test', email='test@test.com', password='test')
        UserProfileFactory(user=self.user)

    def login_user(self):
        self.client.login(username='test', password='test')


class NutritionScreenViewTests(BaseApiText):
    def test_unauthenticated(self):
        response = self.client.get(reverse('api-nutrition-screen'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_response(self):
        self.login_user()

        product = ProductFactory()

        daily_report1 = DailyIntakesReportFactory(user=self.user, date=(datetime.now() - timedelta(days=1)).date())
        daily_report2 = DailyIntakesReportFactory(user=self.user, date=(datetime.now() - timedelta(days=3)).date())
        IntakeFactory(user=self.user, daily_report=daily_report1, product=product, amount_g=100)
        IntakeFactory(user=self.user, daily_report=daily_report2, product=product, amount_g=200)

        DailyIntakesReportFactory(user=self.user, date=(datetime.now() - timedelta(days=2)).date())

        response = self.client.get(reverse('api-nutrition-screen'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data['daily_intakes_reports']), 4)
        self.assertEqual(len(response.data['latest_intakes']), 2)
        self.assertEqual(len(response.data['current_month_daily_reports']), 2)
        self.assertIsNotNone(response.data['today_intakes_report'])


class UserViewTests(BaseApiText):
    def test_unauthenticated(self):
        response = self.client.get(reverse('api-user'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_response_without_summary(self):
        self.login_user()
        response = self.client.get(reverse('api-user'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNone(response.data['is_marketing_allowed'])
        self.assertIsNone(response.data['nutrition_summary']['min_report_date'])
        self.assertIsNone(response.data['nutrition_summary']['max_report_date'])

    def test_response(self):
        self.login_user()

        product = ProductFactory()

        daily_report1 = DailyIntakesReportFactory(user=self.user, date=date(2020, 1, 1))
        daily_report2 = DailyIntakesReportFactory(user=self.user, date=date(2020, 1, 6))
        DailyIntakesReportFactory(user=self.user, date=date(2020, 1, 7))

        IntakeFactory(user=self.user, daily_report=daily_report1, product=product, amount_g=100)
        IntakeFactory(user=self.user, daily_report=daily_report2, product=product, amount_g=100)

        response = self.client.get(reverse('api-user'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nutrition_summary']['min_report_date'], '2020-01-01')
        self.assertEqual(response.data['nutrition_summary']['max_report_date'], '2020-01-06')


class DailyIntakesReportViewTests(BaseApiText):
    def test_daily_intakes_report_unauthenticated(self):
        response = self.client.get(reverse('api-daily-report', kwargs={'date': '2020-01-01'}))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_daily_intakes_report_not_existing_date(self):
        user = UserFactory()
        DailyIntakesReportFactory(user=user, date=date(2020, 1, 1))

        self.login_user()
        response = self.client.get(reverse('api-daily-report', kwargs={'date': '2020-01-01'}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_daily_intakes_report(self):
        DailyIntakesReportFactory(user=self.user, date=date(2020, 1, 1))

        self.login_user()
        response = self.client.get(reverse('api-daily-report', kwargs={'date': '2020-01-01'}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data.get('daily_intakes_report'))


class DailyIntakesReportsViewTests(BaseApiText):
    def test_daily_reports_unauthenticated(self):
        response = self.client.get(reverse('api-daily-reports'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_daily_reports_retrieving_without_arguments(self):
        self.login_user()

        product = ProductFactory()

        daily_report1 = DailyIntakesReportFactory(user=self.user, date=date(2020, 2, 7))
        daily_report2 = DailyIntakesReportFactory(user=self.user, date=date(2020, 2, 8))
        IntakeFactory(user=self.user, daily_report=daily_report1, product=product, amount_g=100)
        IntakeFactory(user=self.user, daily_report=daily_report2, product=product, amount_g=100)

        # Empty should be excluded
        DailyIntakesReportFactory(user=self.user, date=date(2020, 2, 5))

        response = self.client.get(reverse('api-daily-reports'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data['daily_intakes_light_reports']), 2)
        self.assertIsNotNone(response.data['daily_intakes_light_reports'][0].get('nutrient_norms_and_totals'))

    def test_daily_reports_retrieving(self):
        self.login_user()

        product = ProductFactory()

        daily_report1 = DailyIntakesReportFactory(user=self.user, date=date(2020, 1, 7))
        daily_report2 = DailyIntakesReportFactory(user=self.user, date=date(2020, 2, 8))
        IntakeFactory(user=self.user, daily_report=daily_report1, product=product, amount_g=100)
        IntakeFactory(user=self.user, daily_report=daily_report2, product=product, amount_g=100)

        response = self.client.get(reverse('api-daily-reports'), data={'from': '2020-02-01', 'to': '2020-02-08'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data['daily_intakes_light_reports']), 1)
        self.assertEqual(response.data['daily_intakes_light_reports'][0].get('date'), '2020-02-08')


class ProductSearchViewTests(BaseApiText):

    def test_product_search_unauthenticated(self):
        response = self.client.get(reverse('api-products-search'), data={'query': 'apple', 'submit': '1'})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_product_search_empty_query(self):
        ProductFactory(
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
        ProductFactory(
            potassium_mg=1,
            sodium_mg=2,
            phosphorus_mg=3,
            proteins_mg=4,
            energy_kcal=5,
            liquids_g=6,
        )
        excluded_product = ProductFactory(
            name_lt='apple excluded',
            potassium_mg=15,
            sodium_mg=25,
            phosphorus_mg=35,
            proteins_mg=32767,
            energy_kcal=32767,
            liquids_g=32767,
        )

        daily_report = DailyIntakesReportFactory(user=self.user)
        IntakeFactory(user=self.user, daily_report=daily_report, product=product2, amount_g=100)

        self.login_user()
        response = self.client.get(
            reverse('api-products-search'),
            data={
                'query': '',
                'submit': '1',
                'exclude_products': f"{excluded_product.id}",
                'meal_type': 'Lunch',
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['query'], '')
        self.assertEqual(len(response.data['products']), 3)
        self.assertEqual(response.data['products'][0]['id'], product2.id)
        self.assertIsNotNone(response.data['daily_nutrient_norms_and_totals'])

    def test_product_search_without_exclude_param(self):
        ProductFactory()
        DailyIntakesReportFactory(user=self.user)

        self.login_user()

        response_without_exclude = self.client.get(
            reverse('api-products-search'),
            data={
                'query': '',
                'submit': '1'
            }
        )

        self.assertEqual(response_without_exclude.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_without_exclude.data['products']), 1)

    def test_product_search_wit_illegal_exclude_products(self):
        ProductFactory()
        DailyIntakesReportFactory(user=self.user)

        self.login_user()

        response_without_exclude = self.client.get(
            reverse('api-products-search'),
            data={
                'query': '',
                'submit': '1',
                'exclude_products': f"1,2,something,,5",
            }
        )

        self.assertEqual(response_without_exclude.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_without_exclude.data['products']), 1)

    def test_product_search(self):
        product1 = ProductFactory(
            name_lt='apple',
            potassium_mg=15,
            sodium_mg=25,
            phosphorus_mg=35,
            proteins_mg=32767,
            energy_kcal=32767,
            liquids_g=32767,
        )
        product2 = ProductFactory(
            name_lt='apple other',
            potassium_mg=15,
            sodium_mg=25,
            phosphorus_mg=35,
            proteins_mg=32767,
            energy_kcal=32767,
            liquids_g=32767,
        )
        product3 = ProductFactory(
            name_lt='apple other 3',
            potassium_mg=15,
            sodium_mg=25,
            phosphorus_mg=35,
            proteins_mg=32767,
            energy_kcal=32767,
            liquids_g=32767,
        )
        excluded_product = ProductFactory(
            name_lt='apple excluded',
            potassium_mg=15,
            sodium_mg=25,
            phosphorus_mg=35,
            proteins_mg=32767,
            energy_kcal=32767,
            liquids_g=32767,
        )
        ProductFactory(
            name_lt='orange',
            potassium_mg=1,
            sodium_mg=2,
            phosphorus_mg=3,
            proteins_mg=4,
            energy_kcal=5,
            liquids_g=6,
        )

        report1 = DailyIntakesReportFactory(user=self.user)
        IntakeFactory(user=self.user, daily_report=report1, product=product2, amount_g=100,
                      consumed_at=datetime(2021, 2, 10, 10))
        IntakeFactory(user=self.user, daily_report=report1, product=product3, amount_g=100,
                      consumed_at=datetime(2021, 2, 10, 9))

        self.login_user()
        response = self.client.get(reverse('api-products-search'),
                                   data={
                                       'query': 'apple',
                                       'submit': '0',
                                       'exclude_products': f"{excluded_product.id}",
                                   })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['query'], 'apple')
        self.assertEqual(len(response.data['products']), 3)
        self.assertEqual(response.data['products'][0]['name'], product2.name_lt)
        self.assertEqual(response.data['products'][1]['name'], product3.name_lt)
        self.assertEqual(response.data['products'][2]['name'], product1.name_lt)
        self.assertIsNotNone(response.data['daily_nutrient_norms_and_totals'])
