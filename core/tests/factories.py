import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory
from pytz import utc

from core import models


class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Faker('user_name')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')


class UserProfileFactory(DjangoModelFactory):
    class Meta:
        model = models.UserProfile

    gender = factory.Iterator(models.Gender.Female, models.Gender.Male)
    birthday = factory.Faker('date_of_birth')
    year_of_birth = 1960
    height_cm = 185
    weight_kg = 188.8
    chronic_kidney_disease_years = 2
    dialysis_type = factory.Iterator(models.DialysisType.PeriotonicDialysis, models.DialysisType.PostTransplant)


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = models.Product

    name_lt = factory.Faker('user_name')
    name_en = factory.Faker('user_name')
    product_kind = factory.Iterator(models.ProductKind.Food, models.ProductKind.Drink)

    potassium_mg = 10
    sodium_mg = 20
    phosphorus_mg = 30
    proteins_mg = 40
    energy_kcal = 50
    liquids_g = 60
    fat_mg = 70
    carbohydrates_mg = 80


class IntakeFactory(DjangoModelFactory):
    class Meta:
        model = models.Intake

    consumed_at = factory.Faker('date_time', tzinfo=utc)
    amount_g = 150


class DailyIntakesReportFactory(DjangoModelFactory):
    class Meta:
        model = models.DailyIntakesReport

    date = factory.Faker('date')

    daily_norm_potassium_mg = 100
    daily_norm_proteins_mg = 200
    daily_norm_sodium_mg = 300
    daily_norm_phosphorus_mg = 400
    daily_norm_energy_kcal = 500
    daily_norm_liquids_g = 600


class PulseFactory(DjangoModelFactory):
    class Meta:
        model = models.Pulse

    pulse = factory.Faker('pyint', min_value=10, max_value=200)
    measured_at = factory.Faker('date_time_ad')


class BloodPressureFactory(DjangoModelFactory):
    class Meta:
        model = models.BloodPressure

    systolic_blood_pressure = factory.Faker('pyint', min_value=1, max_value=350)
    diastolic_blood_pressure = factory.Faker('pyint', min_value=1, max_value=200)
    measured_at = factory.Faker('date_time_ad')


class DailyHealthStatusFactory(DjangoModelFactory):
    class Meta:
        model = models.DailyHealthStatus
