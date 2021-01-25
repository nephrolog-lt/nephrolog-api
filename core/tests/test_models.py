from datetime import date

from django.test import TestCase

from core.models import UserProfile
from core.tests.factories import UserFactory, UserProfileFactory


class UserProfileTests(TestCase):

    def test_age_calculation(self):
        user = UserFactory()
        user_profile = UserProfileFactory(user=user)
        expected_age = (date.today() - user_profile.birthday).days / 365.25

        queryset = UserProfile.objects.annotate_with_age()

        self.assertAlmostEqual(queryset.first().age, expected_age, delta=1)
