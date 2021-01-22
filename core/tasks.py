import logging

from celery import shared_task

from core.models import DailyHealthStatus, DailyIntakesReport, Intake, Product, ProductKind, User
from core.utils import Datadog

logger = logging.getLogger(__name__)


@shared_task(soft_time_limit=60, autoretry_for=(Exception,), retry_backoff=True)
def sync_product_metrics():
    datadog = Datadog()
    user_with_statistics_queryset = User.get_annotated_with_statistics()

    datadog.gauge('product.users.total', User.objects.count())
    datadog.gauge('product.users.profiles', user_with_statistics_queryset.exclude(profile_count=0).count())
    datadog.gauge('product.users.profiles_with_intakes',
                  user_with_statistics_queryset.exclude(intakes_count=0).count())
    datadog.gauge('product.users.profiles_with_health_status',
                  user_with_statistics_queryset.exclude(daily_health_statuses_count=0).count())

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
