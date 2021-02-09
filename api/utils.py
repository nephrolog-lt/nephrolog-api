import calendar
import datetime
from typing import Optional

import pytz
from django.utils.dateparse import parse_date
from pytz import UnknownTimeZoneError
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request


# https://gist.github.com/waynemoore/1109153
def get_month_day_range(date: datetime.date) -> (datetime.date, datetime.date):
    """
    For a date 'date' returns the start and end date for the month of 'date'.

    Month with 31 days:
    >>> date = datetime.date(2011, 7, 27)
    >>> get_month_day_range(date)
    (datetime.date(2011, 7, 1), datetime.date(2011, 7, 31))

    Month with 28 days:
    >>> date = datetime.date(2011, 2, 15)
    >>> get_month_day_range(date)
    (datetime.date(2011, 2, 1), datetime.date(2011, 2, 28))
    """
    first_day = date.replace(day=1)
    last_day = date.replace(day=calendar.monthrange(date.year, date.month)[1])
    return first_day, last_day


def parse_date_or_validation_error(date_str: Optional[str]) -> datetime.date:
    try:
        parsed_date: datetime.date = parse_date(date_str) if date_str else None

        if parsed_date is None:
            raise ValueError()

        return parsed_date
    except ValueError:
        raise ValidationError("Invalid date")


def parse_date_query_params(request: Request, required: bool = True) -> (datetime.date, datetime.date):
    date_from: str = request.query_params.get('from')
    date_to: str = request.query_params.get('to')

    if not required and date_from is None and date_to is None:
        return None, None

    try:
        parsed_date_from: datetime.date = parse_date_or_validation_error(date_from)
        parsed_date_to: datetime.date = parse_date_or_validation_error(date_to)

        if parsed_date_from is None or parsed_date_to is None or parsed_date_from > parsed_date_to:
            raise ValueError()
    except (ValueError, ValidationError):
        raise ValidationError("Date from and to date arguments invalid")

    return parsed_date_from, parsed_date_to


def parse_time_zone(request: Request) -> datetime.timezone:
    tz_name: str = request.headers.get('time-zone-name', None)

    try:
        return pytz.timezone(tz_name)
    except UnknownTimeZoneError:
        return pytz.timezone('Europe/Vilnius')


def datetime_to_date(dt: datetime.datetime, tz: datetime.timezone) -> datetime.date:
    return dt.astimezone(tz).date()
