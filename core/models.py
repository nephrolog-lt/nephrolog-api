from __future__ import annotations

import datetime
from dataclasses import dataclass
from decimal import Decimal
from functools import reduce
from typing import List, Optional

from ckeditor_uploader.fields import RichTextUploadingField
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AbstractUser, UserManager as AbstractUserManager
from django.contrib.postgres.indexes import GinIndex, GistIndex
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Prefetch, QuerySet, functions
from django.db.models.aggregates import Min
from django.db.transaction import atomic
from django.utils.timezone import now
from sql_util.aggregates import SubqueryCount, SubqueryMax

from core.utils import only_alphanumeric_or_spaces, str_to_ascii
from nephrogo import settings


@dataclass(frozen=True)
class DailyNutrientConsumption:
    total: int
    norm: Optional[int]


@dataclass(frozen=True)
class DailyNutrientNormsAndTotals:
    potassium_mg: DailyNutrientConsumption
    proteins_mg: DailyNutrientConsumption
    sodium_mg: DailyNutrientConsumption
    phosphorus_mg: DailyNutrientConsumption
    energy_kcal: DailyNutrientConsumption
    liquids_ml: DailyNutrientConsumption
    fat_mg: DailyNutrientConsumption
    carbohydrates_mg: DailyNutrientConsumption


class UserQuerySet(models.QuerySet):
    def annotate_with_statistics(self) -> QuerySet[User]:
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

        return self.annotate(
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


class UserManager(AbstractUserManager.from_queryset(UserQuerySet)):
    pass


class User(AbstractUser):
    is_marketing_allowed = models.BooleanField(null=True, blank=True)
    last_app_review_dialog_showed = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    def __str__(self):
        return self.get_username() or self.get_full_name() or self.email

    def _should_show_app_review_dialog(self) -> bool:
        if self.last_app_review_dialog_showed is None and (now() - self.date_joined).days > 3:
            return DailyIntakesReport.filter_for_user(self).count() > 3

        return False

    def show_app_review_dialog_if_needed(self) -> bool:
        if not self._should_show_app_review_dialog():
            return False

        self.last_app_review_dialog_showed = now()
        self.save(update_fields=('last_app_review_dialog_showed',))

        return True

    def nutrition_summary_statistics(self):
        return DailyIntakesReport.summarize_for_user(self)


class Gender(models.TextChoices):
    Male = "Male"
    Female = "Female"


class DialysisType(models.TextChoices):
    Unknown = "Unknown"
    AutomaticPeritonealDialysis = "AutomaticPeritonealDialysis"
    ManualPeritonealDialysis = "ManualPeritonealDialysis"
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


class ChronicKidneyDiseaseAgeInterval(models.TextChoices):
    Unknown = "Unknown", "Unknown"
    BelowOne = "<1", "<1"
    OneToFive = "1-5", "1-5"
    SixToTen = "6-10", "6-10"
    MoreThanTen = ">10", ">10"


class BaseUserProfile(models.Model):
    gender = models.CharField(
        max_length=8,
        choices=Gender.choices,
    )

    height_cm = models.PositiveSmallIntegerField()

    chronic_kidney_disease_age = models.CharField(
        max_length=16,
        choices=ChronicKidneyDiseaseAgeInterval.choices,
        default=ChronicKidneyDiseaseAgeInterval.Unknown,
    )

    chronic_kidney_disease_stage = models.CharField(
        max_length=16,
        choices=ChronicKidneyDiseaseStage.choices,
    )

    dialysis = models.CharField(
        max_length=32,
        choices=DialysisType.choices,
        default=DialysisType.Unknown,
    )

    diabetes_type = models.CharField(
        max_length=16,
        choices=DiabetesType.choices,
        default=DiabetesType.Unknown,
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

    @property
    def _is_diabetic(self) -> bool:
        return self.diabetes_type in (DiabetesType.Type1, DiabetesType.Type2)

    def daily_norm_potassium_mg(self) -> Optional[int]:
        if self.dialysis == DialysisType.Hemodialysis:
            return round(40 * self.perfect_weight_kg)
        if self.dialysis in (DialysisType.AutomaticPeritonealDialysis, DialysisType.ManualPeritonealDialysis):
            return 4000

        return None

    def daily_norm_proteins_mg(self) -> Optional[int]:
        if self.dialysis == DialysisType.NotPerformed:
            if self._is_diabetic:
                return round(800 * self.perfect_weight_kg)
            else:
                return round(600 * self.perfect_weight_kg)

        if self.dialysis in (
                DialysisType.AutomaticPeritonealDialysis,
                DialysisType.ManualPeritonealDialysis,
                DialysisType.Hemodialysis
        ):
            return round(1200 * self.perfect_weight_kg)

        if self.dialysis == DialysisType.PostTransplant:
            return round(800 * self.perfect_weight_kg)

        return None

    def daily_norm_sodium_mg(self) -> Optional[int]:
        return 2300

    def daily_norm_phosphorus_mg(self) -> Optional[int]:
        if self.dialysis in (
                DialysisType.Hemodialysis,
                DialysisType.AutomaticPeritonealDialysis,
                DialysisType.ManualPeritonealDialysis,
                DialysisType.NotPerformed):
            return 1000

        return None

    def daily_norm_energy_kcal(self) -> Optional[int]:
        return None

    def daily_norm_liquids_g_without_urine(self) -> Optional[int]:
        if self.dialysis in (
                DialysisType.Hemodialysis,
                DialysisType.AutomaticPeritonealDialysis,
                DialysisType.ManualPeritonealDialysis,
        ):
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
                'height_cm': user_profile.height_cm,
                'chronic_kidney_disease_age': user_profile.chronic_kidney_disease_age,
                'chronic_kidney_disease_stage': user_profile.chronic_kidney_disease_stage,
                'dialysis': user_profile.dialysis,
                'diabetes_type': user_profile.diabetes_type,
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
    SW = "SW"


class ProductRegion(models.TextChoices):
    LT = "LT"
    DE = "DE"


class ProductQuerySet(models.QuerySet):
    def annotate_with_popularity(self) -> QuerySet[Product]:
        return self.annotate(popularity=SubqueryCount('intakes'))

    def annotate_with_last_consumed_by_user(self, user: AbstractBaseUser) -> QuerySet[Product]:
        return self.annotate(
            last_consumed_by_user=SubqueryMax(
                'intakes__consumed_at',
                filter=models.Q(user=user)
            )
        )


class Product(models.Model):
    name = models.CharField(max_length=128)
    name_en = models.CharField(max_length=128)

    synonyms = models.TextField(blank=True)

    name_search_lt = models.CharField(max_length=128, unique=True)

    product_kind = models.CharField(
        max_length=16,
        choices=ProductKind.choices,
        default=ProductKind.Unknown,
    )

    region = models.CharField(
        max_length=2,
        choices=ProductRegion.choices,
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

    carbohydrates_mg = models.PositiveIntegerField()
    fat_mg = models.PositiveIntegerField()

    density_g_ml = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True,
                                       validators=[validators.MinValueValidator(Decimal('0.01'))])

    raw_id = models.CharField(max_length=64, null=True, blank=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ("-pk",)
        indexes = [
            GinIndex(name="gin_trgm_product_lt", fields=('name_search_lt',), opclasses=("gin_trgm_ops",)),
            GistIndex(name="gist_trgm_product_lt", fields=('name_search_lt',), opclasses=("gist_trgm_ops",)),
            models.Index(fields=['region', 'name', ])
        ]

        constraints = [
            models.UniqueConstraint(fields=['region', 'name'], name='unique_product_name_region'),
            models.UniqueConstraint(fields=['product_source', 'raw_id'], name='unique_product_source_and_raw_id'),
        ]

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.name = self.name.strip()
        self.name_en = self.name_en.strip()
        self.synonyms = self.synonyms.lower().strip()

        search_term_raw = f"{self.name} {self.synonyms}".strip().lower()

        self.name_search_lt = only_alphanumeric_or_spaces(str_to_ascii(search_term_raw))

        super().save(force_insert, force_update, using, update_fields)

    def clean(self) -> None:
        super().clean()

        if self.product_kind == ProductKind.Unknown:
            raise ValidationError('Product kind can not be unknown')

        if self.product_kind == ProductKind.Food and self.density_g_ml is not None:
            raise ValidationError('Food can not contain density')

        if self.product_kind == ProductKind.Drink and self.density_g_ml is None:
            raise ValidationError('Drink must contain density')

    @property
    def liquids_ml(self) -> int:
        density_g_ml = self.density_g_ml or 1

        return round(self.liquids_g / density_g_ml)

    @staticmethod
    def filter_by_user_and_query(
            user: AbstractBaseUser,
            query: Optional[str],
            exclude_product_ids: Optional[List[int]] = None
    ) -> QuerySet[Product]:
        exclude_product_ids = exclude_product_ids or []
        original_query = (query or '').strip().lower()
        query = only_alphanumeric_or_spaces(str_to_ascii(original_query))

        if not query:
            return Product.objects.exclude(pk__in=exclude_product_ids) \
                .filter(region=ProductRegion.LT) \
                .annotate_with_popularity() \
                .annotate_with_last_consumed_by_user(user) \
                .order_by(
                models.F('last_consumed_by_user').desc(nulls_last=True),
                '-popularity'
            )

        query_words = query.split(' ')
        query_filters = map(lambda q: models.Q(name_search_lt__contains=q), query_words)
        query_filter = reduce(lambda a, b: a & b, query_filters)

        first_word = query_words[0]

        return Product.objects.filter(query_filter).exclude(pk__in=exclude_product_ids) \
            .filter(region=ProductRegion.LT) \
            .annotate(
            starts_with_word=models.ExpressionWrapper(
                models.Q(name_search_lt__startswith=first_word),
                output_field=models.BooleanField()
            ),
            starts_with_original_query=models.ExpressionWrapper(
                models.Q(name__istartswith=original_query),
                output_field=models.BooleanField()
            ),
            contains_original_query=models.ExpressionWrapper(
                models.Q(name__icontains=original_query),
                output_field=models.BooleanField()
            )
        ).annotate_with_popularity() \
            .annotate_with_last_consumed_by_user(user) \
            .order_by(
            '-starts_with_original_query',
            '-contains_original_query',
            '-starts_with_word',
            models.F('last_consumed_by_user').desc(nulls_last=True),
            '-popularity'
        )

    def __str__(self):
        return self.name


class DailyIntakesReportQuerySet(models.QuerySet):
    def prefetch_intakes(self) -> DailyIntakesReportQuerySet:
        return self.prefetch_related(Prefetch('intakes', queryset=Intake.objects.select_related_product()))

    def exclude_empty_intakes(self) -> DailyIntakesReportQuerySet:
        return self.exclude(intakes__isnull=True)

    def annotate_with_intakes_count(self) -> QuerySet[DailyIntakesReport]:
        return self.annotate(intakes_count=models.Count('intakes'))

    def annotate_with_nutrient_totals(self) -> QuerySet[DailyIntakesReport]:
        return self.annotate(
            total_potassium_mg=functions.Coalesce(
                models.Sum(
                    models.ExpressionWrapper(
                        models.F("intakes__product__potassium_mg") *
                        models.F("intakes__amount_g") / models.Value(100, output_field=models.IntegerField()),
                        output_field=models.IntegerField()
                    ),
                ), 0),
            total_sodium_mg=functions.Coalesce(
                models.Sum(
                    models.ExpressionWrapper(
                        models.F("intakes__product__sodium_mg") *
                        models.F("intakes__amount_g") / models.Value(100, output_field=models.IntegerField()),
                        output_field=models.IntegerField()
                    ),
                ), 0),
            total_phosphorus_mg=functions.Coalesce(
                models.Sum(
                    models.ExpressionWrapper(
                        models.F("intakes__product__phosphorus_mg") *
                        (models.F("intakes__amount_g") / models.Value(100, output_field=models.IntegerField())),
                        output_field=models.IntegerField()
                    ),
                ), 0),
            total_proteins_mg=functions.Coalesce(models.Sum(
                models.ExpressionWrapper(
                    functions.Cast(models.F("intakes__product__proteins_mg"), output_field=models.IntegerField()) *
                    models.F("intakes__amount_g") / models.Value(100, output_field=models.IntegerField()),
                    output_field=models.IntegerField()
                ),
            ), 0),
            total_energy_kcal=functions.Coalesce(models.Sum(
                models.ExpressionWrapper(
                    functions.Cast(models.F("intakes__product__energy_kcal"), output_field=models.IntegerField()) *
                    models.F("intakes__amount_g") / models.Value(100, output_field=models.IntegerField()),
                    output_field=models.IntegerField()
                ),
            ), 0),
            total_liquids_ml=functions.Coalesce(models.Sum(
                models.ExpressionWrapper(
                    models.ExpressionWrapper(
                        functions.Cast(models.F("intakes__product__liquids_g"),
                                       output_field=models.IntegerField()) / functions.Coalesce(
                            models.F("intakes__product__density_g_ml"), 1),
                        output_field=models.IntegerField()) *
                    models.ExpressionWrapper(models.F("intakes__amount_g"),
                                             output_field=models.IntegerField()
                                             ) / models.Value(100, output_field=models.IntegerField()),
                    output_field=models.IntegerField()
                ),
            ), 0),
            total_fat_mg=functions.Coalesce(models.Sum(
                models.ExpressionWrapper(
                    functions.Cast(models.F("intakes__product__fat_mg"), output_field=models.IntegerField()) *
                    models.ExpressionWrapper(models.F("intakes__amount_g"),
                                             output_field=models.IntegerField()
                                             ) / models.Value(100, output_field=models.IntegerField()),
                    output_field=models.IntegerField()
                ),
            ), 0),
            total_carbohydrates_mg=functions.Coalesce(models.Sum(
                models.ExpressionWrapper(
                    functions.Cast(models.F("intakes__product__carbohydrates_mg"), output_field=models.IntegerField()) *
                    models.ExpressionWrapper(models.F("intakes__amount_g"),
                                             output_field=models.IntegerField()
                                             ) / models.Value(100, output_field=models.IntegerField()),
                    output_field=models.IntegerField()
                ),
            ), 0),
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
    daily_norm_carbohydrates_mg = models.PositiveIntegerField(null=True, blank=True)
    daily_norm_fat_mg = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = DailyIntakesReportQuerySet.as_manager()

    class Meta:
        default_related_name = "daily_intakes_reports"
        constraints = [
            models.UniqueConstraint(fields=['user', 'date'], name='unique_user_date_daily_intakes_report')
        ]

    @staticmethod
    def summarize_for_user(user: AbstractBaseUser) -> dict:
        return DailyIntakesReport.filter_for_user(user).exclude_empty_intakes().aggregate(
            min_report_date=models.Min('date'),
            max_report_date=models.Max('date')
        )

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
    def carbohydrates_mg(self) -> DailyNutrientConsumption:
        return DailyNutrientConsumption(total=self._total_carbohydrates_mg, norm=self.daily_norm_carbohydrates_mg)

    @property
    def fat_mg(self) -> DailyNutrientConsumption:
        return DailyNutrientConsumption(total=self._total_fat_mg, norm=self.daily_norm_fat_mg)

    @property
    def liquids_ml(self) -> DailyNutrientConsumption:
        return DailyNutrientConsumption(total=self._total_liquids_ml, norm=self.daily_norm_liquids_g)

    @property
    def daily_nutrient_norms_and_totals(self) -> DailyNutrientNormsAndTotals:
        return DailyNutrientNormsAndTotals(
            potassium_mg=self.potassium_mg,
            proteins_mg=self.proteins_mg,
            sodium_mg=self.sodium_mg,
            phosphorus_mg=self.phosphorus_mg,
            energy_kcal=self.energy_kcal,
            liquids_ml=self.liquids_ml,
            fat_mg=self.fat_mg,
            carbohydrates_mg=self.carbohydrates_mg,
        )

    @property
    def _total_potassium_mg(self):
        if hasattr(self, 'total_potassium_mg'):
            return self.total_potassium_mg

        return sum(intake.potassium_mg for intake in self.intakes.all())

    @property
    def _total_proteins_mg(self):
        if hasattr(self, 'total_proteins_mg'):
            return self.total_proteins_mg

        return sum(intake.proteins_mg for intake in self.intakes.all())

    @property
    def _total_sodium_mg(self):
        if hasattr(self, 'total_sodium_mg'):
            return self.total_sodium_mg

        return sum(intake.sodium_mg for intake in self.intakes.all())

    @property
    def _total_phosphorus_mg(self):
        if hasattr(self, 'total_phosphorus_mg'):
            return self.total_phosphorus_mg

        return sum(intake.phosphorus_mg for intake in self.intakes.all())

    @property
    def _total_energy_kcal(self):
        if hasattr(self, 'total_energy_kcal'):
            return self.total_energy_kcal

        return sum(intake.energy_kcal for intake in self.intakes.all())

    @property
    def _total_liquids_ml(self):
        if hasattr(self, 'total_liquids_ml'):
            return self.total_liquids_ml

        return sum(intake.liquids_ml for intake in self.intakes.all())

    @property
    def _total_carbohydrates_mg(self):
        if hasattr(self, 'total_carbohydrates_mg'):
            return self.total_carbohydrates_mg

        return sum(intake.carbohydrates_mg for intake in self.intakes.all())

    @property
    def _total_fat_mg(self):
        if hasattr(self, 'total_fat_mg'):
            return self.total_fat_mg

        return sum(intake.fat_mg for intake in self.intakes.all())

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
    def get_latest_daily_nutrient_norms_and_totals(user: AbstractBaseUser) -> DailyNutrientNormsAndTotals:
        report = DailyIntakesReport.filter_for_user(user).annotate_with_nutrient_totals().order_by('-date').first()

        if report is None:
            raise ValueError(
                'Unable to get latest nutrient norms and totals. Make sure at least one report is created.')

        return report.daily_nutrient_norms_and_totals

    @staticmethod
    def get_for_user_between_dates(user: AbstractBaseUser, date_from: datetime.date,
                                   date_to: datetime.date):
        return DailyIntakesReport.filter_for_user(user=user).filter(
            date__range=(date_from, date_to)).order_by('date')

    @staticmethod
    def filter_for_user(user: AbstractBaseUser):
        return DailyIntakesReport.objects.filter(user=user)


class MealType(models.TextChoices):
    Unknown = "Unknown"
    Breakfast = "Breakfast"
    Lunch = "Lunch"
    Dinner = "Dinner"
    Snack = "Snack"


class IntakeQuerySet(models.QuerySet):
    def select_related_product(self) -> IntakeQuerySet:
        return self.select_related('product')


class Intake(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+')
    daily_report = models.ForeignKey(DailyIntakesReport, on_delete=models.CASCADE, related_name='intakes')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='intakes')

    meal_type = models.CharField(
        max_length=16,
        choices=MealType.choices,
        default=MealType.Unknown,
    )

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

    @property
    def liquids_ml(self) -> int:
        return int(self.product.liquids_ml * self._amount_nutrient_ratio)

    @property
    def fat_mg(self) -> int:
        return int(self.product.fat_mg * self._amount_nutrient_ratio)

    @property
    def carbohydrates_mg(self) -> int:
        return int(self.product.carbohydrates_mg * self._amount_nutrient_ratio)

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
    def prefetch_all_related_fields(self) -> DailyHealthStatusQuerySet:
        return self.prefetch_related('swellings', 'blood_pressures', 'pulses', 'manual_peritoneal_dialysis')

    def prefetch_blood_pressure_and_pulse(self) -> DailyHealthStatusQuerySet:
        return self.prefetch_related('blood_pressures', 'pulses')

    def filter_manual_peritoneal_dialysis(self) -> DailyHealthStatusQuerySet:
        return self.exclude(manual_peritoneal_dialysis__isnull=True)


class DailyHealthStatus(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()

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
    def get_or_create_for_user_and_date(user: AbstractBaseUser, date: datetime.date) -> DailyHealthStatus:
        health_status, _ = DailyHealthStatus.objects.get_or_create(user=user, date=date)

        return health_status

    @staticmethod
    def get_between_dates_for_user(user: AbstractBaseUser, date_from: datetime.date,
                                   date_to: datetime.date) -> DailyHealthStatusQuerySet:
        return DailyHealthStatus.filter_for_user(user).filter(
            date__range=(date_from, date_to)).prefetch_all_related_fields().order_by('date')

    def __str__(self):
        return f"{self.user} {self.date}"


class BloodPressure(models.Model):
    daily_health_status = models.ForeignKey(DailyHealthStatus, on_delete=models.CASCADE, related_name='blood_pressures')
    systolic_blood_pressure = models.PositiveSmallIntegerField(
        validators=[
            validators.MinValueValidator(1),
            validators.MaxValueValidator(350),
        ]
    )
    diastolic_blood_pressure = models.PositiveSmallIntegerField(
        validators=[
            validators.MinValueValidator(1),
            validators.MaxValueValidator(200),
        ],
    )

    measured_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['daily_health_status', 'measured_at'],
                name='unique_blood_pressure_health_status_measure_at'
            )
        ]

    @staticmethod
    def filter_for_user(user: AbstractBaseUser) -> QuerySet[BloodPressure]:
        return BloodPressure.objects.filter(daily_health_status__user=user)

    def __str__(self):
        return f"{self.systolic_blood_pressure} / {self.diastolic_blood_pressure} {self.daily_health_status}"


class Pulse(models.Model):
    daily_health_status = models.ForeignKey(DailyHealthStatus, on_delete=models.CASCADE, related_name='pulses')
    pulse = models.PositiveSmallIntegerField(
        validators=[
            validators.MinValueValidator(10),
            validators.MaxValueValidator(200),
        ]
    )

    measured_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['daily_health_status', 'measured_at'],
                name='unique_pulse_health_status_measure_at'
            )
        ]

    @staticmethod
    def filter_for_user(user: AbstractBaseUser) -> QuerySet[Pulse]:
        return Pulse.objects.filter(daily_health_status__user=user)

    def __str__(self):
        return f"{self.pulse} {self.daily_health_status}"


class ProductSearchLog(models.Model):
    query = models.CharField(max_length=32)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=False, related_name='+')

    product1 = models.ForeignKey(Product, on_delete=models.CASCADE, db_index=False, null=True, blank=True,
                                 related_name='+')
    product2 = models.ForeignKey(Product, on_delete=models.CASCADE, db_index=False, null=True, blank=True,
                                 related_name='+')
    product3 = models.ForeignKey(Product, on_delete=models.CASCADE, db_index=False, null=True, blank=True,
                                 related_name='+')
    results_count = models.PositiveSmallIntegerField()

    meal_type = models.CharField(
        max_length=16,
        choices=MealType.choices,
        default=MealType.Unknown,
    )

    submit = models.BooleanField(null=True, blank=True)
    excluded_products_count = models.SmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-pk",)

    @staticmethod
    def insert_from_product_search(
            query: str, products: QuerySet[Product], user: AbstractBaseUser,
            submit: Optional[bool], excluded_products_count: int = 0,
            meal_type: Optional[MealType] = None
    ):
        meal_type = meal_type or MealType.Unknown
        results_count = len(products)
        product1 = products[0] if results_count >= 1 else None
        product2 = products[1] if results_count >= 2 else None
        product3 = products[2] if results_count >= 3 else None

        ProductSearchLog.objects.create(query=query[:32], user=user, product1=product1, product2=product2,
                                        product3=product3, results_count=results_count, submit=submit,
                                        excluded_products_count=excluded_products_count, meal_type=meal_type)

    def __str__(self):
        return f"{self.user} {self.query}"


class GeneralRecommendationCategory(models.Model):
    name_lt = models.CharField(max_length=128)
    order = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("order", "pk")

    def __str__(self):
        return self.name_lt


class GeneralRecommendationSubcategory(models.Model):
    category = models.ForeignKey(GeneralRecommendationCategory, on_delete=models.CASCADE, related_name='subcategories')
    name_lt = models.CharField(max_length=256)
    order = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("order", "pk")

    def __str__(self):
        return self.name_lt


class GeneralRecommendation(models.Model):
    subcategory = models.ForeignKey(GeneralRecommendationSubcategory, on_delete=models.PROTECT,
                                    related_name='recommendations')
    name_lt = models.CharField(max_length=256)
    body_lt = RichTextUploadingField()

    order = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("order", "pk")

    def __str__(self):
        return self.name_lt

    def full_body(self) -> str:
        return f"<h3>{self.name_lt}</h3>{self.body_lt}"


class GeneralRecommendationRead(models.Model):
    general_recommendation = models.ForeignKey(
        GeneralRecommendation,
        on_delete=models.CASCADE,
        db_index=False,
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+')
    reads = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-pk",)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'general_recommendation'],
                name='unique_user_and_recommendation_for_read'
            )
        ]

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.reads = (self.reads or 0) + 1

        super().save(force_insert, force_update, using, update_fields)


class DialysisSolution(models.TextChoices):
    Unknown = "Unknown"
    Yellow = "Yellow"
    Green = "Green"
    Orange = "Orange"
    Blue = "Blue"
    Purple = "Purple"


class DialysateColor(models.TextChoices):
    Unknown = "Unknown"
    Transparent = "Transparent"
    Pink = "Pink"
    CloudyYellowish = "CloudyYellowish"
    Greenish = "Greenish"
    Brown = "Brown"
    CloudyWhite = "CloudyWhite"


class ManualPeritonealDialysisQuerySet(models.QuerySet):
    def select_related_fields(self) -> ManualPeritonealDialysisQuerySet:
        return self.select_related('blood_pressure', 'pulse', 'daily_health_status')

    def filter_not_completed(self) -> ManualPeritonealDialysisQuerySet:
        return self.filter(is_completed=False)


# noinspection PyUnresolvedReferences
class ManualPeritonealDialysisManager(models.Manager.from_queryset(ManualPeritonealDialysisQuerySet)):
    def get_queryset(self):
        return super().get_queryset().annotate(
            finished_at=models.Window(
                functions.Lag('started_at'),
                order_by=models.F('started_at').desc(),
                partition_by=models.F('daily_health_status__user')
            )
        )


class ManualPeritonealDialysis(models.Model):
    daily_health_status = models.ForeignKey(
        DailyHealthStatus,
        on_delete=models.CASCADE,
    )
    daily_intakes_report = models.ForeignKey(
        DailyIntakesReport,
        on_delete=models.CASCADE,
    )

    is_completed = models.BooleanField(default=False)

    started_at = models.DateTimeField()

    dialysis_solution = models.CharField(
        max_length=16,
        choices=DialysisSolution.choices,
        default=DialysisSolution.Unknown,
    )

    solution_in_ml = models.PositiveSmallIntegerField()
    solution_out_ml = models.PositiveSmallIntegerField(null=True, blank=True)

    dialysate_color = models.CharField(
        max_length=16,
        choices=DialysateColor.choices,
        default=DialysateColor.Unknown,
    )

    notes = models.TextField(blank=True)

    finished_at_deprecated = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ManualPeritonealDialysisManager()

    class Meta:
        default_related_name = "manual_peritoneal_dialysis"
        ordering = ("-pk",)

    def clean(self) -> None:
        super().clean()

        if self.is_completed and self.solution_out_ml is None:
            raise ValidationError('Make sure that by completeing dialysis all required fields are filled out')

    @staticmethod
    def filter_for_user(user: AbstractBaseUser) -> QuerySet[ManualPeritonealDialysis]:
        return ManualPeritonealDialysis.objects.filter(daily_health_status__user=user)


class AutomaticPeritonealDialysisQuerySet(models.QuerySet):
    def prefetch_all_related(self) -> AutomaticPeritonealDialysisQuerySet:
        return self.prefetch_related(
            Prefetch(
                'daily_intakes_report',
                queryset=DailyIntakesReport.objects.annotate_with_nutrient_totals()
            ),
            Prefetch(
                'daily_health_status',
                queryset=DailyHealthStatus.objects.prefetch_all_related_fields()
            ),
        )

    def filter_not_completed(self) -> AutomaticPeritonealDialysisQuerySet:
        return self.filter(is_completed=False)


class AutomaticPeritonealDialysis(models.Model):
    daily_health_status = models.OneToOneField(
        DailyHealthStatus,
        on_delete=models.CASCADE,
    )
    daily_intakes_report = models.OneToOneField(
        DailyIntakesReport,
        on_delete=models.CASCADE,
    )

    is_completed = models.BooleanField(default=False)

    started_at = models.DateTimeField()

    solution_yellow_in_ml = models.PositiveSmallIntegerField(default=0)
    solution_green_in_ml = models.PositiveSmallIntegerField(default=0)
    solution_orange_in_ml = models.PositiveSmallIntegerField(default=0)
    solution_blue_in_ml = models.PositiveSmallIntegerField(default=0)
    solution_purple_in_ml = models.PositiveSmallIntegerField(default=0)

    initial_draining_ml = models.PositiveSmallIntegerField(null=True, blank=True)
    total_drain_volume_ml = models.PositiveSmallIntegerField(null=True, blank=True)
    last_fill_ml = models.PositiveSmallIntegerField(null=True, blank=True)
    total_ultrafiltration_ml = models.PositiveIntegerField(null=True, blank=True)

    dialysate_color = models.CharField(
        max_length=16,
        choices=DialysateColor.choices,
        default=DialysateColor.Unknown,
    )

    notes = models.TextField(blank=True)

    finished_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AutomaticPeritonealDialysisQuerySet.as_manager()

    class Meta:
        default_related_name = "automatic_peritoneal_dialysis"
        ordering = ("-pk",)

    @staticmethod
    def filter_for_user(user: AbstractBaseUser) -> QuerySet[AutomaticPeritonealDialysis]:
        return AutomaticPeritonealDialysis.objects.filter(daily_health_status__user=user)

    @staticmethod
    def filter_for_user_between_dates(
            user: AbstractBaseUser,
            date_from: datetime.date,
            date_to: datetime.date
    ) -> AutomaticPeritonealDialysisQuerySet:
        return AutomaticPeritonealDialysis.filter_for_user(user).filter(
            daily_health_status__date__range=(date_from, date_to)
        )
