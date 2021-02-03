from __future__ import annotations

import datetime
from dataclasses import dataclass
from decimal import Decimal
from itertools import chain
from typing import Optional

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.indexes import GinIndex, GistIndex
from django.contrib.postgres.search import TrigramSimilarity
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Prefetch, QuerySet, functions
from django.db.models.aggregates import Max, Min
from django.db.transaction import atomic
from django.utils.timezone import now

from core.utils import str_to_ascii
from nephrogo import settings


@dataclass(frozen=True)
class DailyNutrientConsumption:
    total: int
    norm: Optional[int]


class User(AbstractUser):
    def __str__(self):
        return self.get_username() or self.get_full_name() or self.email

    @staticmethod
    def get_annotated_with_statistics() -> QuerySet[User]:
        intakes_count = User.objects.annotate(
            intakes_count=models.Count('daily_intakes_reports__intakes')
        ).filter(pk=models.OuterRef('pk'))

        daily_intakes_reports_count = User.objects.annotate(
            daily_intakes_reports_count=models.Count('daily_intakes_reports')
        ).filter(pk=models.OuterRef('pk'))

        profile_count = User.objects.annotate(
            profile_count=models.Count('profile')
        ).filter(pk=models.OuterRef('pk'))

        daily_health_statuses_count = User.objects.annotate(
            daily_health_statuses_count=models.Count('daily_health_statuses')
        ).filter(pk=models.OuterRef('pk'))

        historical_profiles_count = User.objects.annotate(
            historical_profiles_count=models.Count('historical_profiles')
        ).filter(pk=models.OuterRef('pk'))

        return User.objects.annotate(
            intakes_count=models.Subquery(
                intakes_count.values('intakes_count'),
                output_field=models.IntegerField()
            ),
            daily_intakes_reports_count=models.Subquery(
                daily_intakes_reports_count.values('daily_intakes_reports_count'),
                output_field=models.IntegerField()
            ),
            daily_health_statuses_count=models.Subquery(
                daily_health_statuses_count.values('daily_health_statuses_count'),
                output_field=models.IntegerField()
            ),
            profile_count=models.Subquery(
                profile_count.values('profile_count'),
                output_field=models.IntegerField()
            ),
            historical_profiles_count=models.Subquery(
                historical_profiles_count.values('historical_profiles_count'),
                output_field=models.IntegerField()
            ),

        )


class Gender(models.TextChoices):
    Male = "Male"
    Female = "Female"


class DialysisType(models.TextChoices):
    Unknown = "Unknown"
    PeriotonicDialysis = "PeriotonicDialysis"
    Hemodialysis = "Hemodialysis"
    PostTransplant = "PostTransplant"
    NotPerformed = "NotPerformed"


class ChronicKidneyDiseaseStage(models.TextChoices):
    Unknown = "Unknown"
    Stage1 = "Stage1"
    Stage2 = "Stage2"
    Stage3 = "Stage3"
    Stage4 = "Stage4"
    Stage5 = "Stage5"


class DiabetesType(models.TextChoices):
    Unknown = "Unknown"
    Type1 = "Type1"
    Type2 = "Type2"
    No = "No"


class DiabetesComplications(models.TextChoices):
    Unknown = "Unknown"
    No = "No"
    Yes = "Yes"


class BaseUserProfile(models.Model):
    gender = models.CharField(
        max_length=8,
        choices=Gender.choices,
    )
    # TODO remove birthday in the future. Change made 02-03
    birthday = models.DateField(null=True, blank=True)
    year_of_birth = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[validators.MinValueValidator(1920), validators.MaxValueValidator(2003)]
    )
    height_cm = models.PositiveSmallIntegerField()
    # TODO remove in the future. Change made 02-03
    weight_kg = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True,
                                    validators=[validators.MinValueValidator(Decimal('10'))])

    chronic_kidney_disease_years = models.PositiveSmallIntegerField()
    chronic_kidney_disease_stage = models.CharField(
        max_length=16,
        choices=ChronicKidneyDiseaseStage.choices,
    )
    dialysis_type = models.CharField(
        max_length=32,
        choices=DialysisType.choices,
    )

    diabetes_years = models.PositiveSmallIntegerField(null=True, blank=True)
    diabetes_type = models.CharField(
        max_length=16,
        choices=DiabetesType.choices,
        default=DiabetesType.Unknown,
    )
    diabetes_complications = models.CharField(
        max_length=8,
        choices=DiabetesComplications.choices,
        default=DiabetesComplications.Unknown,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    _base_height = 152
    _cm_per_inch = 2.54

    _female_weight_increase_constant = 2.27
    _base_female_weight = 45.36

    _base_male_weight = 48.08
    _male_weight_increase_constant = 2.72

    class Meta:
        abstract = True

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.diabetes_type in (DiabetesType.Unknown, DiabetesType.No):
            self.diabetes_complications = DiabetesComplications.Unknown
            self.diabetes_years = None

        if self.birthday and self.year_of_birth is None:
            self.year_of_birth = self.birthday.year

        super().save(force_insert, force_update, using, update_fields)

    @property
    def _is_diabetic(self) -> bool:
        return self.diabetes_type in (DiabetesType.Type1, DiabetesType.Type2)

    def daily_norm_potassium_mg(self) -> Optional[int]:
        if self.dialysis_type == DialysisType.Hemodialysis:
            return round(40 * self.perfect_weight_kg)
        if self.dialysis_type == DialysisType.PeriotonicDialysis:
            return 4000

        return None

    def daily_norm_proteins_mg(self) -> Optional[int]:
        if self.dialysis_type == DialysisType.NotPerformed:
            if self._is_diabetic:
                return round(800 * self.perfect_weight_kg)
            else:
                return round(600 * self.perfect_weight_kg)

        if self.dialysis_type in (DialysisType.PeriotonicDialysis, DialysisType.Hemodialysis):
            return round(1200 * self.perfect_weight_kg)

        if self.dialysis_type == DialysisType.PostTransplant:
            return round(800 * self.perfect_weight_kg)

        return None

    def daily_norm_sodium_mg(self) -> Optional[int]:
        return 2300

    def daily_norm_phosphorus_mg(self) -> Optional[int]:
        if self.dialysis_type in (
                DialysisType.Hemodialysis, DialysisType.PeriotonicDialysis, DialysisType.NotPerformed):
            return 1000

        return None

    def daily_norm_energy_kcal(self) -> Optional[int]:
        return round(35 * self.perfect_weight_kg)

    def daily_norm_liquids_g_without_urine(self) -> Optional[int]:
        if self.dialysis_type in (DialysisType.Hemodialysis, DialysisType.PeriotonicDialysis):
            return 1000

        return None

    @property
    def _weight_increase_constant(self):
        if self.gender == Gender.Female:
            return self._female_weight_increase_constant

        return self._male_weight_increase_constant

    @property
    def _base_weight(self):
        if self.gender == Gender.Female:
            return self._base_female_weight

        return self._base_male_weight

    @property
    def perfect_weight_kg(self) -> float:
        return (max(self.height_cm - self._base_height,
                    0) / self._cm_per_inch) * self._weight_increase_constant + self._base_weight


class UserProfileQuerySet(models.QuerySet):
    def annotate_with_age(self) -> QuerySet[UserProfile]:
        current_year = now().year
        return self.annotate(
            age=models.ExpressionWrapper(
                models.Value(current_year, output_field=models.IntegerField()) - models.F('year_of_birth'),
                output_field=models.IntegerField()
            )
        )

    def filter_diabetics(self) -> UserProfileQuerySet:
        return self.filter(diabetes_type__in=(DiabetesType.Type1, DiabetesType.Type2))


class UserProfile(BaseUserProfile):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')

    objects = UserProfileQuerySet.as_manager()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        with atomic():
            super().save(force_insert, force_update, using, update_fields)

            HistoricalUserProfile.create_or_update_historical_user_profile(user_profile=self)

        DailyIntakesReport.recalculate_daily_norms_for_date_if_exists(user=self.user, date=datetime.datetime.now())

    @staticmethod
    def get_for_user(user: AbstractUser) -> UserProfile:
        return UserProfile.objects.get(user=user)


class HistoricalUserProfile(BaseUserProfile):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()

    class Meta:
        default_related_name = "historical_profiles"

        constraints = [
            models.UniqueConstraint(fields=['user', 'date'], name='unique_user_date_historical_user_profile')
        ]

    # Setting date without user timezone information is hack, but it's acceptable
    @staticmethod
    def create_or_update_historical_user_profile(user_profile: UserProfile) -> HistoricalUserProfile:
        historical_profile, _ = HistoricalUserProfile.objects.update_or_create(
            user=user_profile.user,
            date=datetime.date.today(),
            defaults={
                'gender': user_profile.gender,
                'birthday': user_profile.birthday,
                'year_of_birth': user_profile.year_of_birth,
                'height_cm': user_profile.height_cm,
                'weight_kg': user_profile.weight_kg,
                'chronic_kidney_disease_years': user_profile.chronic_kidney_disease_years,
                'chronic_kidney_disease_stage': user_profile.chronic_kidney_disease_stage,
                'dialysis_type': user_profile.dialysis_type,
                'diabetes_complications': user_profile.diabetes_complications,
                'created_at': user_profile.created_at,
                'updated_at': user_profile.updated_at,
            })

        return historical_profile

    @staticmethod
    def get_nearest_historical_profile_for_date(user: AbstractBaseUser, date: datetime.date) -> HistoricalUserProfile:
        historical_profile_for_date = HistoricalUserProfile.objects.filter(user=user, date__lte=date).order_by(
            '-date').first()

        if historical_profile_for_date:
            return historical_profile_for_date

        return HistoricalUserProfile.objects.filter(user=user).exclude(date__lte=date).order_by('date')[:1].get()


# Nutrition
class ProductKind(models.TextChoices):
    Unknown = "Unknown"
    Food = "Food"
    Drink = "Drink"


class ProductSource(models.TextChoices):
    LT = "LT"
    DN = "DN"


class ProductQuerySet(models.QuerySet):
    def annotate_with_popularity(self) -> QuerySet[Product]:
        return self.annotate(popularity=models.Count('intakes'))


class Product(models.Model):
    name_lt = models.CharField(max_length=128, unique=True)
    name_en = models.CharField(max_length=128, unique=True)

    name_search_lt = models.CharField(max_length=128, unique=True)

    product_kind = models.CharField(
        max_length=16,
        choices=ProductKind.choices,
        default=ProductKind.Unknown,
    )

    product_source = models.CharField(
        max_length=2,
        choices=ProductSource.choices,
        default=ProductSource.LT,
        editable=False
    )

    potassium_mg = models.DecimalField(max_digits=7, decimal_places=2,
                                       validators=[validators.MinValueValidator(Decimal('0'))])
    sodium_mg = models.DecimalField(max_digits=7, decimal_places=2,
                                    validators=[validators.MinValueValidator(Decimal('0'))])
    phosphorus_mg = models.DecimalField(max_digits=7, decimal_places=2,
                                        validators=[validators.MinValueValidator(Decimal('0'))])
    proteins_mg = models.PositiveIntegerField()
    energy_kcal = models.PositiveSmallIntegerField()
    liquids_g = models.PositiveSmallIntegerField()

    density_g_ml = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True,
                                       validators=[validators.MinValueValidator(Decimal('0.01'))])

    raw_id = models.CharField(max_length=64, null=True, blank=True, editable=False, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ("-pk",)
        indexes = [
            GinIndex(name="gin_trgm_product_lt", fields=('name_search_lt',), opclasses=("gin_trgm_ops",)),
            GistIndex(name="gist_trgm_product_lt", fields=('name_search_lt',), opclasses=("gist_trgm_ops",)),
        ]

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.name_search_lt = str_to_ascii(self.name_lt).lower()

        super().save(force_insert, force_update, using, update_fields)

    @staticmethod
    def filter_by_user_and_query(user: AbstractBaseUser, query: Optional[str], limit: int) -> QuerySet[Product]:
        query = str_to_ascii(query.strip()).lower() if query else None

        if query:
            return Product.objects.annotate(similarity=TrigramSimilarity('name_search_lt', query)).filter(
                similarity__gt=0.1).order_by('-similarity')[:limit]

        last_consumed_products: QuerySet[Product] = Product.last_consumed_products_by_user(user)[:limit]

        remaining = max(0, limit - len(last_consumed_products))
        if remaining == 0:
            return last_consumed_products

        popular_products = Product.objects.exclude(pk__in=last_consumed_products) \
                               .annotate_with_popularity().order_by('-popularity')[:remaining]

        return chain(last_consumed_products, popular_products)

    @staticmethod
    def last_consumed_products_by_user(user: AbstractBaseUser):
        return Product.objects.filter(intakes__user=user).annotate(
            max_consumed_at=Max('intakes__consumed_at')).order_by('-max_consumed_at')

    def __str__(self):
        return self.name_lt


class DailyIntakesReportQuerySet(models.QuerySet):
    def prefetch_intakes(self) -> DailyIntakesReportQuerySet:
        return self.prefetch_related(Prefetch('intakes', queryset=Intake.objects.select_related_product()))

    def exclude_empty_intakes(self) -> DailyIntakesReportQuerySet:
        return self.exclude(intakes__isnull=True)

    def annotate_with_intakes_count(self) -> QuerySet[DailyIntakesReport]:
        return self.annotate(intakes_count=models.Count('intakes'))

    def annotate_with_nutrient_totals(self) -> QuerySet[DailyIntakesReport]:
        return self.annotate(
            total_potassium_mg=models.Sum(
                models.ExpressionWrapper(
                    models.F("intakes__product__potassium_mg") *
                    models.F("intakes__amount_g") / models.Value(100, output_field=models.IntegerField()),
                    output_field=models.IntegerField()
                ),
            ),
            total_sodium_mg=models.Sum(
                models.ExpressionWrapper(
                    models.F("intakes__product__sodium_mg") *
                    models.F("intakes__amount_g") / models.Value(100, output_field=models.IntegerField()),
                    output_field=models.IntegerField()
                ),
            ),
            total_phosphorus_mg=models.Sum(
                models.ExpressionWrapper(
                    models.F("intakes__product__phosphorus_mg") *
                    (models.F("intakes__amount_g") / models.Value(100, output_field=models.IntegerField())),
                    output_field=models.IntegerField()
                ),
            ),
            total_proteins_mg=models.Sum(
                models.ExpressionWrapper(
                    functions.Cast(models.F("intakes__product__proteins_mg"), output_field=models.IntegerField()) *
                    models.F("intakes__amount_g") / models.Value(100, output_field=models.IntegerField()),
                    output_field=models.IntegerField()
                ),
            ),
            total_energy_kcal=models.Sum(
                models.ExpressionWrapper(
                    functions.Cast(models.F("intakes__product__energy_kcal"), output_field=models.IntegerField()) *
                    models.F("intakes__amount_g") / models.Value(100, output_field=models.IntegerField()),
                    output_field=models.IntegerField()
                ),
            ),
            total_liquids_g=models.Sum(
                models.ExpressionWrapper(
                    functions.Cast(models.F("intakes__product__liquids_g"), output_field=models.IntegerField()) *
                    models.ExpressionWrapper(models.F("intakes__amount_g"),
                                             output_field=models.IntegerField()
                                             ) / models.Value(100, output_field=models.IntegerField()),
                    output_field=models.IntegerField()
                ),
            ),
        )


class DailyIntakesReport(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()

    daily_norm_potassium_mg = models.PositiveIntegerField(null=True, blank=True)
    daily_norm_proteins_mg = models.PositiveIntegerField(null=True, blank=True)
    daily_norm_sodium_mg = models.PositiveIntegerField(null=True, blank=True)
    daily_norm_phosphorus_mg = models.PositiveIntegerField(null=True, blank=True)
    daily_norm_energy_kcal = models.PositiveIntegerField(null=True, blank=True)
    daily_norm_liquids_g = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = DailyIntakesReportQuerySet.as_manager()

    class Meta:
        default_related_name = "daily_intakes_reports"
        constraints = [
            models.UniqueConstraint(fields=['user', 'date'], name='unique_user_date_daily_intakes_report')
        ]

    @staticmethod
    def get_earliest_report_date(user: AbstractBaseUser) -> Optional[datetime.date]:
        return DailyIntakesReport.filter_for_user(user).aggregate(min_date=Min('date'))['min_date']

    @property
    def potassium_mg(self) -> DailyNutrientConsumption:
        return DailyNutrientConsumption(total=self._total_potassium_mg, norm=self.daily_norm_potassium_mg)

    @property
    def proteins_mg(self) -> DailyNutrientConsumption:
        return DailyNutrientConsumption(total=self._total_proteins_mg, norm=self.daily_norm_proteins_mg)

    @property
    def sodium_mg(self) -> DailyNutrientConsumption:
        return DailyNutrientConsumption(total=self._total_sodium_mg, norm=self.daily_norm_sodium_mg)

    @property
    def phosphorus_mg(self) -> DailyNutrientConsumption:
        return DailyNutrientConsumption(total=self._total_phosphorus_mg, norm=self.daily_norm_phosphorus_mg)

    @property
    def energy_kcal(self) -> DailyNutrientConsumption:
        return DailyNutrientConsumption(total=self._total_energy_kcal, norm=self.daily_norm_energy_kcal)

    @property
    def liquids_g(self) -> DailyNutrientConsumption:
        return DailyNutrientConsumption(total=self._total_liquids_g, norm=self.daily_norm_liquids_g)

    @property
    def liquids_ml(self) -> DailyNutrientConsumption:
        return self.liquids_g

    @property
    def _total_potassium_mg(self):
        return sum(intake.potassium_mg for intake in self.intakes.all())

    @property
    def _total_proteins_mg(self):
        return sum(intake.proteins_mg for intake in self.intakes.all())

    @property
    def _total_sodium_mg(self):
        return sum(intake.sodium_mg for intake in self.intakes.all())

    @property
    def _total_phosphorus_mg(self):
        return sum(intake.phosphorus_mg for intake in self.intakes.all())

    @property
    def _total_energy_kcal(self):
        return sum(intake.energy_kcal for intake in self.intakes.all())

    @property
    def _total_liquids_g(self):
        return sum(intake.liquids_g for intake in self.intakes.all())

    def recalculate_daily_norms(self):
        profile = HistoricalUserProfile.get_nearest_historical_profile_for_date(self.user, self.date)

        if not profile:
            return

        health_status = DailyHealthStatus.get_for_user_and_date(user=self.user, date=self.date)

        self.daily_norm_potassium_mg = profile.daily_norm_potassium_mg()
        self.daily_norm_proteins_mg = profile.daily_norm_proteins_mg()
        self.daily_norm_sodium_mg = profile.daily_norm_sodium_mg()
        self.daily_norm_phosphorus_mg = profile.daily_norm_phosphorus_mg()
        self.daily_norm_energy_kcal = profile.daily_norm_energy_kcal()
        self.daily_norm_liquids_g = profile.daily_norm_liquids_g_without_urine()

        if self.daily_norm_liquids_g and health_status and health_status.urine_ml:
            self.daily_norm_liquids_g += health_status.urine_ml

        self.save(
            update_fields=(
                'daily_norm_potassium_mg',
                'daily_norm_proteins_mg',
                'daily_norm_sodium_mg',
                'daily_norm_phosphorus_mg',
                'daily_norm_energy_kcal',
                'daily_norm_liquids_g'
            )
        )

    @staticmethod
    def recalculate_daily_norms_for_date_if_exists(user: AbstractBaseUser, date: datetime.date):
        report = DailyIntakesReport.objects.filter(user=user, date=date).first()

        if report:
            report.recalculate_daily_norms()

    @staticmethod
    def get_or_create_for_user_and_date(user: AbstractBaseUser, date: datetime.date) -> DailyIntakesReport:
        with atomic():
            report, created = DailyIntakesReport.objects.get_or_create(user=user, date=date)

            if created:
                report.recalculate_daily_norms()

        return report

    @staticmethod
    def get_for_user_between_dates(user: AbstractBaseUser, date_from: datetime.date,
                                   date_to: datetime.date):
        return DailyIntakesReport.filter_for_user(user=user).filter(
            date__range=(date_from, date_to)).prefetch_intakes().order_by('date')

    @staticmethod
    def filter_for_user(user: AbstractBaseUser):
        return DailyIntakesReport.objects.filter(user=user)


class IntakeQuerySet(models.QuerySet):
    def select_related_product(self) -> IntakeQuerySet:
        return self.select_related('product')


class Intake(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+')
    daily_report = models.ForeignKey(DailyIntakesReport, on_delete=models.CASCADE, related_name='intakes')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='intakes')
    consumed_at = models.DateTimeField()
    amount_g = models.PositiveSmallIntegerField(validators=(validators.MinValueValidator(1),))
    amount_ml = models.PositiveSmallIntegerField(null=True, blank=True, validators=(validators.MinValueValidator(1),))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = IntakeQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(fields=('user', '-consumed_at')),
        ]

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.amount_ml is None and self.product.density_g_ml:
            self.amount_ml = round(self.amount_g / self.product.density_g_ml)

        super().save(force_insert, force_update, using, update_fields)

    @staticmethod
    def get_latest_user_intakes(user: AbstractBaseUser) -> IntakeQuerySet:
        return Intake.objects.filter(user=user).select_related_product().order_by('-consumed_at')

    @property
    def _amount_nutrient_ratio(self) -> Decimal:
        return Decimal(self.amount_g / 100.0)

    @property
    def potassium_mg(self) -> int:
        return int(self.product.potassium_mg * self._amount_nutrient_ratio)

    @property
    def proteins_mg(self) -> int:
        return int(self.product.proteins_mg * self._amount_nutrient_ratio)

    @property
    def sodium_mg(self) -> int:
        return int(self.product.sodium_mg * self._amount_nutrient_ratio)

    @property
    def phosphorus_mg(self) -> int:
        return int(self.product.phosphorus_mg * self._amount_nutrient_ratio)

    @property
    def energy_kcal(self) -> int:
        return int(self.product.energy_kcal * self._amount_nutrient_ratio)

    @property
    def liquids_g(self) -> int:
        return int(self.product.liquids_g * self._amount_nutrient_ratio)

    def __str__(self):
        return str(self.product)


# Health status
class SwellingDifficulty(models.TextChoices):
    Unknown = "Unknown"
    Difficulty0 = "0+"
    Difficulty1 = "1+"
    Difficulty2 = "2+"
    Difficulty3 = "3+"
    Difficulty4 = "4+"


class WellFeeling(models.TextChoices):
    Unknown = "Unknown"
    Perfect = "Perfect"
    Good = "Good"
    Average = "Average"
    Bad = "Bad"
    VeryBad = "VeryBad"


class Appetite(models.TextChoices):
    Unknown = "Unknown"
    Perfect = "Perfect"
    Good = "Good"
    Average = "Average"
    Bad = "Bad"
    VeryBad = "VeryBad"


class ShortnessOfBreath(models.TextChoices):
    Unknown = "Unknown"
    No = "No"
    Light = "Light"
    Average = "Average"
    Severe = "Severe"
    Backbreaking = "Backbreaking"


class SwellingEnum(models.TextChoices):
    Unknown = "Unknown"
    Eyes = "Eyes"
    WholeFace = "WholeFace"
    HandBreadth = "HandBreadth"
    Hands = "Hands"
    Belly = "Belly"
    Knees = "Knees"
    Foot = "Foot"
    WholeLegs = "WholeLegs"


class Swelling(models.Model):
    swelling = models.CharField(
        max_length=16,
        choices=SwellingEnum.choices,
    )

    def __str__(self):
        return self.swelling


class DailyHealthStatusQuerySet(models.QuerySet):
    def prefetch_swellings(self) -> DailyHealthStatusQuerySet:
        return self.prefetch_related('swellings')


class DailyHealthStatus(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()

    systolic_blood_pressure = models.PositiveSmallIntegerField(null=True, blank=True)
    diastolic_blood_pressure = models.PositiveSmallIntegerField(null=True, blank=True)

    weight_kg = models.DecimalField(null=True, blank=True, max_digits=4, decimal_places=1,
                                    validators=[validators.MinValueValidator(Decimal('10'))])

    glucose = models.DecimalField(null=True, blank=True, max_digits=7, decimal_places=2,
                                  validators=[validators.MinValueValidator(Decimal('0'))])
    urine_ml = models.PositiveSmallIntegerField(null=True, blank=True)

    swellings = models.ManyToManyField(Swelling, blank=True)

    swelling_difficulty = models.CharField(
        max_length=16,
        choices=SwellingDifficulty.choices,
        default=SwellingDifficulty.Unknown,
    )

    well_feeling = models.CharField(
        max_length=16,
        choices=WellFeeling.choices,
        default=WellFeeling.Unknown,
    )
    appetite = models.CharField(
        max_length=16,
        choices=Appetite.choices,
        default=Appetite.Unknown,
    )
    shortness_of_breath = models.CharField(
        max_length=16,
        choices=ShortnessOfBreath.choices,
        default=ShortnessOfBreath.Unknown,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = DailyHealthStatusQuerySet.as_manager()

    class Meta:
        default_related_name = "daily_health_statuses"
        constraints = [
            models.UniqueConstraint(fields=['user', 'date'], name='unique_user_date_daily_health_status')
        ]

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save(force_insert, force_update, using, update_fields)

        DailyIntakesReport.recalculate_daily_norms_for_date_if_exists(user=self.user, date=self.date)

    def clean(self) -> None:
        super().clean()

        if (self.systolic_blood_pressure is None) != (self.diastolic_blood_pressure is None):
            raise ValidationError('Pass both systolic and diastolic blood pressure')

    @staticmethod
    def get_earliest_user_entry_date(user: AbstractBaseUser) -> Optional[datetime.date]:
        return DailyHealthStatus.filter_for_user(user).aggregate(min_date=Min('date'))['min_date']

    @staticmethod
    def has_any_statuses(user: AbstractBaseUser) -> bool:
        return DailyHealthStatus.filter_for_user(user).exists()

    @staticmethod
    def filter_for_user(user: AbstractBaseUser) -> DailyHealthStatusQuerySet:
        return DailyHealthStatus.objects.filter(user=user)

    @staticmethod
    def get_for_user_and_date(user: AbstractBaseUser, date: datetime.date) -> Optional[DailyHealthStatus]:
        return DailyHealthStatus.filter_for_user(user).filter(date=date).first()

    @staticmethod
    def get_between_dates_for_user(user: AbstractBaseUser, date_from: datetime.date,
                                   date_to: datetime.date) -> DailyHealthStatusQuerySet:
        return DailyHealthStatus.filter_for_user(user).filter(
            date__range=(date_from, date_to)).prefetch_swellings().order_by('date')

    def __str__(self):
        return f"{self.user} {self.date}"
