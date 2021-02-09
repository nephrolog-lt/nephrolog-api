from datetime import date, timezone, datetime
from typing import Optional

import pytz
from django.utils.dateparse import parse_date
from pytz import UnknownTimeZoneError
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request


def parse_date_or_validation_error(date_str: Optional[str]) -> date:
    try:
        parsed_date: date = parse_date(date_str) if date_str else None

        if parsed_date is None:
            raise ValueError()

        return parsed_date
    except ValueError:
        raise ValidationError("Invalid date")


def parse_date_query_params(request: Request, required: bool = True) -> (date, date):
    date_from: str = request.query_params.get('from')
    date_to: str = request.query_params.get('to')

    if not required and date_from is None and date_to is None:
        return None, None

    try:
        parsed_date_from: date = parse_date_or_validation_error(date_from)
        parsed_date_to: date = parse_date_or_validation_error(date_to)

        if parsed_date_from is None or parsed_date_to is None or parsed_date_from > parsed_date_to:
            raise ValueError()
    except (ValueError, ValidationError):
        raise ValidationError("Date from and to date arguments invalid")

    return parsed_date_from, parsed_date_to


def parse_time_zone(request: Request) -> timezone:
    tz_name: str = request.headers.get('time-zone-name', None)

    try:
        return pytz.timezone(tz_name)
    except UnknownTimeZoneError:
        return pytz.timezone('Europe/Vilnius')


def datetime_to_date(dt: datetime, tz: timezone) -> date:
    return dt.astimezone(tz).date()
