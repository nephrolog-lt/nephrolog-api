from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import List, Optional

from rest_framework.request import Request

from api import utils
from api.utils import parse_date_query_params
from core.models import DailyHealthStatus, DailyIntakesReport, Intake, UserProfile, Product, \
    DailyNutrientNormsAndTotals, ProductSearchLog


@dataclass(frozen=True)
class DailyIntakesReportsLightResponse:
    daily_intakes_light_reports: List[DailyIntakesReport]

    @staticmethod
    def from_api_request(request: Request) -> DailyIntakesReportsLightResponse:
        date_from, date_to = parse_date_query_params(request, required=False)

        daily_intakes_reports = DailyIntakesReport.get_for_user_between_dates(request.user, date_from, date_to)

        # TODO this is for backward compatability. Remove in the future 02-09
        if date_from is None or date_to is None:
            daily_intakes_reports = DailyIntakesReport.filter_for_user(request.user)

        daily_intakes_reports = daily_intakes_reports.annotate_with_nutrient_totals().exclude_empty_intakes()

        return DailyIntakesReportsLightResponse(
            daily_intakes_light_reports=daily_intakes_reports
        )


@dataclass(frozen=True)
class DailyIntakesReportResponse:
    daily_intakes_report: DailyIntakesReport


@dataclass(frozen=True)
class NutrientScreenResponse:
    today_intakes_report: DailyIntakesReport
    latest_intakes: List[Intake]
    daily_intakes_reports: List[DailyIntakesReport]
    current_month_daily_reports: List[DailyIntakesReport]

    @staticmethod
    def from_api_request(request: Request) -> NutrientScreenResponse:
        user = request.user
        tz = utils.parse_time_zone(request)

        now = datetime.datetime.now(tz)

        month_start, month_end = utils.get_month_day_range(now.date())

        from_date = (now - datetime.timedelta(days=6)).date()
        to_date = now.date()

        DailyIntakesReport.get_or_create_for_user_and_date(user, to_date)

        current_month_daily_reports = DailyIntakesReport.get_for_user_between_dates(
            request.user,
            month_start,
            month_end
        ).annotate_with_nutrient_totals().exclude_empty_intakes()

        daily_intakes_reports = DailyIntakesReport.get_for_user_between_dates(request.user, from_date,
                                                                              to_date).prefetch_intakes()
        today_intakes_report = max(daily_intakes_reports, key=lambda r: r.date)
        latest_intakes = Intake.get_latest_user_intakes(user)[:3]

        return NutrientScreenResponse(
            today_intakes_report=today_intakes_report,
            daily_intakes_reports=daily_intakes_reports,
            latest_intakes=latest_intakes,
            current_month_daily_reports=current_month_daily_reports,
        )


@dataclass(frozen=True)
class NutrientWeeklyScreenResponse:
    earliest_report_date: Optional[datetime.date]
    daily_intakes_reports: List[DailyIntakesReport]

    @staticmethod
    def from_api_request(request: Request) -> NutrientWeeklyScreenResponse:
        user = request.user
        date_from, date_to = parse_date_query_params(request)

        daily_intakes_reports = DailyIntakesReport.get_for_user_between_dates(user, date_from,
                                                                              date_to).prefetch_intakes()
        earliest_report_date = DailyIntakesReport.get_earliest_report_date(user)

        return NutrientWeeklyScreenResponse(
            earliest_report_date=earliest_report_date,
            daily_intakes_reports=daily_intakes_reports
        )


@dataclass(frozen=True)
class HealthStatusScreenResponse:
    has_any_statuses: bool
    daily_health_statuses: List[DailyHealthStatus]

    @staticmethod
    def from_api_request(request: Request) -> HealthStatusScreenResponse:
        user = request.user
        tz = utils.parse_time_zone(request)

        now = datetime.datetime.now(tz)

        from_date = (now - datetime.timedelta(days=6)).date()
        to_date = now.date()

        daily_health_statuses = DailyHealthStatus.get_between_dates_for_user(user, from_date, to_date)
        has_any_statuses = bool(daily_health_statuses) or DailyHealthStatus.has_any_statuses(user)

        return HealthStatusScreenResponse(
            has_any_statuses=has_any_statuses,
            daily_health_statuses=daily_health_statuses
        )


@dataclass(frozen=True)
class HealthStatusWeeklyResponse:
    earliest_health_status_date: Optional[datetime.date]
    daily_health_statuses: List[DailyHealthStatus]

    @staticmethod
    def from_api_request(request: Request) -> HealthStatusWeeklyResponse:
        user = request.user
        date_from, date_to = parse_date_query_params(request)

        daily_health_statuses = DailyHealthStatus.get_between_dates_for_user(user, date_from, date_to)
        earliest_health_status_date = DailyHealthStatus.get_earliest_user_entry_date(user)

        return HealthStatusWeeklyResponse(
            earliest_health_status_date=earliest_health_status_date,
            daily_health_statuses=daily_health_statuses
        )


@dataclass(frozen=True)
class ProductSearchResponse:
    products: List[Product]
    query: str
    daily_nutrient_norms_and_totals: DailyNutrientNormsAndTotals

    @staticmethod
    # noinspection DuplicatedCode
    def from_api_request(request: Request, limit: int) -> ProductSearchResponse:
        query = request.query_params.get('query', '')
        user = request.user

        products = Product.filter_by_user_and_query(user, query)[:limit]
        daily_nutrient_norms_and_totals = DailyIntakesReport.get_latest_daily_nutrient_norms_and_totals(user)

        if query:
            submit_str = request.query_params.get('submit', None)

            submit = None
            if submit_str in ('0', 'false'):
                submit = False
            elif submit_str in ('1', 'true'):
                submit = True

            ProductSearchLog.insert_from_product_search(query, products, user, submit)

        return ProductSearchResponse(
            products=products,
            query=query,
            daily_nutrient_norms_and_totals=daily_nutrient_norms_and_totals,
        )
