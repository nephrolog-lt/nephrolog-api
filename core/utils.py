import time
from typing import List, Optional, Union
import datadog

from unidecode import unidecode

from nephrogo import settings


def str_to_ascii(s: str) -> str:
    return unidecode(s)


class Datadog:
    class __DatadogSingleton:
        def __init__(self):
            datadog.initialize(**settings.DATADOG_SETTINGS)

    instance = None

    def __init__(self):
        if not Datadog.instance:
            Datadog.instance = Datadog.__DatadogSingleton()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def gauge(self, metric_name: str, value: Union[int, float], tags: Optional[List[str]] = None):
        options = {
            'metric': metric_name,
            'points': [(int(time.time()), value)],
            'type': 'gauge',
        }

        if tags:
            options['tags'] = tags

        return datadog.api.Metric.send(**options)
