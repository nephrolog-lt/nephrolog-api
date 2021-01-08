from datetime import date, timezone, datetime

import pytz
from django.utils.dateparse import parse_date
from pytz import UnknownTimeZoneError
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request


def parse_date_query_params(request: Request) -> (date, date):
    date_from: str = request.query_params.get('from')
    date_to: str = request.query_params.get('to')

    try:
        parsed_date_from: date = parse_date(date_from) if date_from else None
        parsed_date_to: date = parse_date(date_to) if date_to else None

        if parsed_date_from is None or parsed_date_to is None or parsed_date_from > parsed_date_to:
            raise ValueError()
    except ValueError:
        raise ValidationError("Date from and to date arguments invalid")

    return parsed_date_from, parsed_date_to


def parse_time_zone(request: Request) -> timezone:
    tz_name: str = request.headers.get('Time-Zone-Name', None)

    try:
        return pytz.timezone(tz_name)
    except UnknownTimeZoneError:
        return pytz.timezone('Europe/Vilnius')


def datetime_to_date(dt: datetime, tz: timezone) -> date:
    return dt.astimezone(tz).date()
