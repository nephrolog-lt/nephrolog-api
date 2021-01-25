import logging
from datetime import timedelta

from celery import shared_task
from django.db.models.aggregates import Count

from core.models import Appetite, DailyHealthStatus, DailyIntakesReport, DiabetesType, HistoricalUserProfile, Intake, \
    Product, \
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

    def _gauge_aggregated_user_profile_metric(field_name: str, only_with_diabetes: bool = False):
        queryset = UserProfile.objects.all()
        if only_with_diabetes:
            queryset = queryset.filter(diabetes_type__in=(DiabetesType.Type1, DiabetesType.Type2))

        agg_users = queryset.values(field_name).annotate(total=Count(field_name)).order_by('total')
        for metric in agg_users:
            datadog.gauge(f'product.users.profiles.{field_name}', metric['total'],
                          tags=[f'{field_name}:{metric[field_name]}'])

    user_with_statistics_queryset = User.get_annotated_with_statistics()
    user_with_statistics_and_profile_queryset = user_with_statistics_queryset.exclude(profile_count=0)

    datadog.gauge('product.users.total', User.objects.count())
    datadog.gauge('product.users.profiles', user_with_statistics_and_profile_queryset.count())
    datadog.gauge('product.users.profiles.historical', HistoricalUserProfile.objects.count())
    datadog.gauge('product.users.profiles_with_intakes',
                  user_with_statistics_and_profile_queryset.exclude(intakes_count=0).count())
    datadog.gauge('product.users.profiles_with_health_status',
                  user_with_statistics_and_profile_queryset.exclude(daily_health_statuses_count=0).count())

    _gauge_aggregated_user_profile_metric('gender')
    _gauge_aggregated_user_profile_metric('chronic_kidney_disease_stage')
    _gauge_aggregated_user_profile_metric('dialysis_type')
    _gauge_aggregated_user_profile_metric('diabetes_type')
    _gauge_aggregated_user_profile_metric('diabetes_complications', only_with_diabetes=True)

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
