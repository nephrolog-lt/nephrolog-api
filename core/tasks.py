import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(soft_time_limit=30)
def hello():
    print("Hello")

    return {
        'Hello': 1
    }
