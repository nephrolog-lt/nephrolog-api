import logging

from celery import shared_task

from core.models import User
from core.utils import Datadog

logger = logging.getLogger(__name__)


@shared_task(soft_time_limit=60, autoretry_for=(Exception,), retry_backoff=True)
def sync_product_metrics():
    user_with_statistics_queryset = User.get_annotated_with_statistics()

    Datadog().gauge('product.users.total', User.objects.count())
    Datadog().gauge('product.users.profiles', user_with_statistics_queryset.exclude(profile_count=0).count())
    Datadog().gauge('product.users.profiles_with_intakes',
                    user_with_statistics_queryset.exclude(intakes_count=0).count())
