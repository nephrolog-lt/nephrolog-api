import logging
from datetime import timedelta

from celery import shared_task
from django.db.models.aggregates import Count

from core.models import Appetite, DailyHealthStatus, DailyIntakesReport, HistoricalUserProfile, Intake, Product, \
    ProductKind, \
    ShortnessOfBreath, SwellingDifficulty, User, \
    UserProfile, WellFeeling
from core.utils import Datadog
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(soft_time_limit=60, autoretry_for=(Exception,), retry_backoff=True)
def sync_product_metrics():
    datadog = Datadog()
    now = timezone.now()

    user_with_statistics_queryset = User.get_annotated_with_statistics()
    user_with_statistics_and_profile_queryset = user_with_statistics_queryset.exclude(profile_count=0)

    datadog.gauge('product.users.total', User.objects.count())
    datadog.gauge('product.users.profiles', user_with_statistics_and_profile_queryset.count())
    datadog.gauge('product.users.profiles.historical', HistoricalUserProfile.objects.count())
    datadog.gauge('product.users.profiles_with_intakes',
                  user_with_statistics_and_profile_queryset.exclude(intakes_count=0).count())
    datadog.gauge('product.users.profiles_with_health_status',
                  user_with_statistics_and_profile_queryset.exclude(daily_health_statuses_count=0).count())

    users_by_gender = UserProfile.objects.values('gender').annotate(total=Count('gender')).order_by('total')
    for gender in users_by_gender:
        datadog.gauge('product.users.profiles.gender', gender['total'], tags=[f'gender:{gender["gender"]}'])

    users_by_chronic_kidney_disease_stage = UserProfile.objects.values('chronic_kidney_disease_stage').annotate(
        total=Count('chronic_kidney_disease_stage')).order_by('total')
    for by_disease_stage in users_by_chronic_kidney_disease_stage:
        datadog.gauge('product.users.profiles.chronic_kidney_disease_stage', by_disease_stage['total'],
                      tags=[f'chronic_kidney_disease_stage:{by_disease_stage["chronic_kidney_disease_stage"]}'])

    users_by_dialysis_type = UserProfile.objects.values('dialysis_type').annotate(
        total=Count('dialysis_type')).order_by('total')
    for by_dialysis_type in users_by_dialysis_type:
        datadog.gauge('product.users.profiles.dialysis_type', by_dialysis_type['total'],
                      tags=[f'dialysis_type:{by_dialysis_type["dialysis_type"]}'])

    users_by_diabetes_complications = UserProfile.objects.values('diabetes_complications').annotate(
        total=Count('diabetes_complications')).order_by('total')
    for by_diabetes_complications in users_by_diabetes_complications:
        datadog.gauge('product.users.profiles.diabetes_complications', by_diabetes_complications['total'],
                      tags=[f'diabetes_complications:{by_diabetes_complications["diabetes_complications"]}'])

    datadog.gauge('product.users.last_sign_in.24_hours',
                  user_with_statistics_and_profile_queryset.filter(last_login__gte=now - timedelta(days=1)).count())
    datadog.gauge('product.users.last_sign_in.3_days',
                  user_with_statistics_and_profile_queryset.filter(last_login__gte=now - timedelta(days=3)).count())
    datadog.gauge('product.users.last_sign_in.14_days',
                  user_with_statistics_and_profile_queryset.filter(last_login__gte=now - timedelta(days=14)).count())

    datadog.gauge('product.health_status.total', DailyHealthStatus.objects.count())

    datadog.gauge(
        'product.intakes.reports.total', DailyIntakesReport.objects.exclude(intakes__isnull=True).count())

    for kind in ProductKind.values:
        datadog.gauge(
            'product.intakes.total',
            Intake.objects.filter(product__product_kind=kind).count(),
            tags=[f'kind:{kind}']
        )

        datadog.gauge(
            'product.products.total',
            Product.objects.filter(product_kind=kind).count(),
            tags=[f'kind:{kind}']
        )

    datadog.gauge('product.health_status.blood_pressure',
                  DailyHealthStatus.objects.filter(systolic_blood_pressure__isnull=False).count())

    datadog.gauge('product.health_status.weight_kg',
                  DailyHealthStatus.objects.filter(weight_kg__isnull=False).count())

    datadog.gauge('product.health_status.glucose',
                  DailyHealthStatus.objects.filter(glucose__isnull=False).count())

    datadog.gauge('product.health_status.urine_ml',
                  DailyHealthStatus.objects.filter(urine_ml__isnull=False).count())

    datadog.gauge('product.health_status.swellings',
                  DailyHealthStatus.objects.filter(swellings__isnull=False).count())

    datadog.gauge('product.health_status.swelling_difficulty',
                  DailyHealthStatus.objects.exclude(swelling_difficulty=SwellingDifficulty.Unknown).count())

    datadog.gauge('product.health_status.well_feeling',
                  DailyHealthStatus.objects.exclude(well_feeling=WellFeeling.Unknown).count())

    datadog.gauge('product.health_status.appetite',
                  DailyHealthStatus.objects.exclude(appetite=Appetite.Unknown).count())

    datadog.gauge('product.health_status.shortness_of_breath',
                  DailyHealthStatus.objects.exclude(shortness_of_breath=ShortnessOfBreath.Unknown).count())
