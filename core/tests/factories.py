import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

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
    height_cm = 185
    weight_kg = 188.8
    chronic_kidney_disease_years = 2
    dialysis_type = factory.Iterator(models.DialysisType.PeriotonicDialysis, models.DialysisType.PostTransplant)
