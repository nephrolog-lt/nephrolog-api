import logging
from datetime import timedelta

from celery import shared_task
from django.db.models import F
from django.db.models.aggregates import Count, Sum
from django.utils import timezone

from core.models import Appetite, AutomaticPeritonealDialysis, BloodPressure, Country, DailyHealthStatus, \
    DailyIntakesReport, \
    GeneralRecommendation, GeneralRecommendationRead, HistoricalUserProfile, Intake, \
    ManualPeritonealDialysis, MissingProduct, Product, \
    ProductKind, \
    Pulse, ShortnessOfBreath, SwellingDifficulty, User, \
    UserProfile, WellFeeling
from core.utils import Datadog

logger = logging.getLogger(__name__)


@shared_task(soft_time_limit=60, autoretry_for=(Exception,), retry_backoff=True)
def sync_product_metrics():
    datadog = Datadog()
    now = timezone.now()

    def _gauge_daily_norm(field_name: str, metric_name: str):
        total_field_name = field_name if field_name != 'liquids_g' else 'liquids_ml'

        intake_reports_with_totals = DailyIntakesReport.objects.exclude_empty_intakes() \
            .annotate_with_nutrient_totals()

        reports_with_indicator = intake_reports_with_totals.filter(**{f'daily_norm_{field_name}__isnull': False})
        exceeded = reports_with_indicator.filter(**{f'daily_norm_{field_name}__lt': F(f'total_{total_field_name}')})

        datadog.gauge(
            f'product.nutrition.norms.{metric_name}.total', reports_with_indicator.count())
        datadog.gauge(
            f'product.nutrition.norms.{metric_name}.exceeded', exceeded.count())

    # noinspection PyShadowingNames
    def _gauge_aggregated_user_profile_metric(field_name: str, country: Country):
        agg_users = UserProfile.objects.filter(user__country=country).values(field_name) \
            .annotate(total=Count(field_name)) \
            .order_by('total')

        for metric in agg_users:
            datadog.gauge(f'product.users.profiles.{field_name}', metric['total'],
                          tags=[f'{field_name}:{metric[field_name]}', f'country_code:{country.code}'])

    for country in Country.objects.all():
        country_tag = f'country_code:{country.code}'

        user_with_statistics_queryset = User.objects.annotate_with_statistics().filter(country=country)
        user_with_statistics_and_profile_queryset = user_with_statistics_queryset.exclude(profile_count=0)

        datadog.gauge(
            'product.users.total',
            user_with_statistics_queryset.count(),
            tags=[country_tag],
        )
        datadog.gauge(
            'product.users.profiles',
            user_with_statistics_and_profile_queryset.count(),
            tags=[country_tag],
        )

        datadog.gauge(
            'product.users.profiles.diabetics',
            UserProfile.objects.filter(user__country=country).filter_diabetics().count(),
            tags=[country_tag],
        )
        datadog.gauge(
            'product.users.profiles.historical',
            HistoricalUserProfile.objects.filter(user__country=country).count(),
            tags=[country_tag],
        )

        datadog.gauge(
            'product.users.profiles_with_intakes',
            user_with_statistics_and_profile_queryset.exclude(intakes_count=0).count(),
            tags=[country_tag],
        )
        datadog.gauge(
            'product.users.profiles_with_health_status',
            user_with_statistics_and_profile_queryset.exclude(daily_health_statuses_count=0).count(),
            tags=[country_tag],
        )

        datadog.gauge(
            'product.users.last_sign_in.24_hours',
            user_with_statistics_and_profile_queryset.filter(last_login__gte=now - timedelta(days=1)).count(),
            tags=[country_tag],
        )
        datadog.gauge(
            'product.users.last_sign_in.3_days',
            user_with_statistics_and_profile_queryset.filter(last_login__gte=now - timedelta(days=3)).count(),
            tags=[country_tag],
        )
        datadog.gauge(
            'product.users.last_sign_in.14_days',
            user_with_statistics_and_profile_queryset.filter(last_login__gte=now - timedelta(days=14)).count(),
            tags=[country_tag],
        )

        _gauge_aggregated_user_profile_metric('gender', country=country)
        _gauge_aggregated_user_profile_metric('chronic_kidney_disease_age', country=country)
        _gauge_aggregated_user_profile_metric('chronic_kidney_disease_stage', country=country)
        _gauge_aggregated_user_profile_metric('dialysis', country=country)
        _gauge_aggregated_user_profile_metric('diabetes_type', country=country)

    datadog.gauge('product.health_status.total', DailyHealthStatus.objects.count())

    datadog.gauge(
        'product.intakes.reports.total', DailyIntakesReport.objects.exclude_empty_intakes().count())

    _gauge_daily_norm('potassium_mg', 'potassium')
    _gauge_daily_norm('sodium_mg', 'sodium')
    _gauge_daily_norm('phosphorus_mg', 'phosphorus')
    _gauge_daily_norm('proteins_mg', 'proteins')
    _gauge_daily_norm('energy_kcal', 'energy')
    _gauge_daily_norm('liquids_g', 'liquids')

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

    datadog.gauge(
        'product.products.missing',
        MissingProduct.objects.count(),
    )

    datadog.gauge('product.health_status.blood_pressure', BloodPressure.objects.count())
    datadog.gauge('product.health_status.pulse', Pulse.objects.count())

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

    datadog.gauge('product.dialysis.manual.total', ManualPeritonealDialysis.objects.count())
    datadog.gauge('product.dialysis.automatic.total', AutomaticPeritonealDialysis.objects.count())
    datadog.gauge('product.general_recommendations.total', GeneralRecommendation.objects.count())
    datadog.gauge('product.general_recommendations.reads.total',
                  GeneralRecommendationRead.objects.aggregate(Sum('reads'))['reads__sum'])
    datadog.gauge('product.general_recommendations.reads.unique_total',
                  GeneralRecommendationRead.objects.count())
