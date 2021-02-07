from datetime import date

from rest_framework.test import APITestCase, override_settings
from django.urls import reverse
from rest_framework import status

from core.models import DailyIntakesReport, UserProfile, User
from core.tests.factories import DailyIntakesReportFactory, IntakeFactory, ProductFactory, UserFactory, \
    UserProfileFactory
from rest_framework.test import APIClient, APIRequestFactory


class ProductSearchViewTests(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user('test', email='test@test.com', password='test')

    def login_user(self):
        self.client.login(username='test', password='test')

    def test_product_search_unauthenticated(self):
        response = self.client.get(reverse('api-products-search'), data={'query': 'apple', 'submit': '1'})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_product_search_empty_query(self):
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
        product3 = ProductFactory(
            potassium_mg=1,
            sodium_mg=2,
            phosphorus_mg=3,
            proteins_mg=4,
            energy_kcal=5,
            liquids_g=6,
        )

        daily_report = DailyIntakesReportFactory(user=self.user)
        IntakeFactory(user=self.user, daily_report=daily_report, product=product2, amount_g=100)

        self.login_user()
        response = self.client.get(reverse('api-products-search'), data={'query': '', 'submit': '1'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['query'], '')
        self.assertEqual(len(response.data['products']), 3)
        self.assertEqual(response.data['products'][0]['id'], product2.id)
        self.assertIsNotNone(response.data['daily_nutrient_norms_and_totals'])

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
            name_lt='orange',
            potassium_mg=1,
            sodium_mg=2,
            phosphorus_mg=3,
            proteins_mg=4,
            energy_kcal=5,
            liquids_g=6,
        )

        DailyIntakesReportFactory(user=self.user)

        self.login_user()
        response = self.client.get(reverse('api-products-search'), data={'query': 'apple', 'submit': '0'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['query'], 'apple')
        self.assertEqual(len(response.data['products']), 1)
        self.assertEqual(response.data['products'][0]['id'], product1.id)
        self.assertIsNotNone(response.data['daily_nutrient_norms_and_totals'])
