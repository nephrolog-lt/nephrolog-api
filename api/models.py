from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Iterable, List, Optional

from django.db.models import QuerySet
from rest_framework.request import Request

from api import utils
from api.utils import parse_date_query_params
from core.models import AutomaticPeritonealDialysis, DailyHealthStatus, DailyHealthStatusQuerySet, DailyIntakesReport, \
    DailyNutrientNormsAndTotals, GeneralRecommendationCategory, Intake, ManualPeritonealDialysis, MealType, Product, \
    ProductSearchLog, UserProfile


@dataclass(frozen=True)
class AutomaticPeritonealDialysisScreenResponse:
    last_week_health_statuses: DailyHealthStatusQuerySet
    last_week_light_nutrition_reports: QuerySet[DailyIntakesReport]
    last_peritoneal_dialysis: Optional[AutomaticPeritonealDialysis]
    peritoneal_dialysis_in_progress: Optional[AutomaticPeritonealDialysis]

    # noinspection DuplicatedCode
    @staticmethod
    def from_api_request(request: Request) -> AutomaticPeritonealDialysisScreenResponse:
        tz = utils.parse_time_zone(request)

        now = datetime.datetime.now(tz)

        from_date = (now - datetime.timedelta(days=6)).date()
        to_date = now.date()

        last_week_health_statuses = DailyHealthStatus.get_between_dates_for_user(
            request.user,
            from_date,
            to_date
        ).prefetch_all_related_fields()

        last_week_light_nutrition_reports = DailyIntakesReport.get_for_user_between_dates(
            request.user,
            from_date,
            to_date
        ).annotate_with_nutrient_totals()

        peritoneal_dialysis_in_progress = AutomaticPeritonealDialysis.filter_for_user(request.user) \
            .filter_not_completed().prefetch_all_related().first()

        last_peritoneal_dialysis = peritoneal_dialysis_in_progress

        if last_peritoneal_dialysis is None:
            last_peritoneal_dialysis = AutomaticPeritonealDialysis.filter_for_user(
                request.user
            ).prefetch_all_related().order_by('-started_at').first()

        return AutomaticPeritonealDialysisScreenResponse(
            last_week_health_statuses=last_week_health_statuses,
            last_week_light_nutrition_reports=last_week_light_nutrition_reports,
            peritoneal_dialysis_in_progress=peritoneal_dialysis_in_progress,
            last_peritoneal_dialysis=last_peritoneal_dialysis,
        )


@dataclass(frozen=True)
class AutomaticPeritonealDialysisPeriodResponse:
    peritoneal_dialysis: QuerySet[AutomaticPeritonealDialysis]

    @staticmethod
    def from_api_request(request: Request) -> AutomaticPeritonealDialysisPeriodResponse:
        date_from, date_to = parse_date_query_params(request)

        peritoneal_dialysis = AutomaticPeritonealDialysis.filter_for_user_between_dates(
            request.user,
            date_from,
            date_to
        ).prefetch_all_related().order_by('-pk')

        return AutomaticPeritonealDialysisPeriodResponse(
            peritoneal_dialysis=peritoneal_dialysis,
        )


@dataclass(frozen=True)
class ManualPeritonealDialysisScreenResponse:
    last_peritoneal_dialysis: Iterable[ManualPeritonealDialysis]
    last_week_health_statuses: DailyHealthStatusQuerySet
    last_week_light_nutrition_reports: QuerySet[DailyIntakesReport]
    peritoneal_dialysis_in_progress: Optional[ManualPeritonealDialysis]

    # noinspection DuplicatedCode
    @staticmethod
    def from_api_request(request: Request) -> ManualPeritonealDialysisScreenResponse:
        tz = utils.parse_time_zone(request)

        now = datetime.datetime.now(tz)

        from_date = (now - datetime.timedelta(days=6)).date()
        to_date = now.date()

        weekly_health_statuses = DailyHealthStatus.get_between_dates_for_user(
            request.user,
            from_date,
            to_date
        ).prefetch_all_related_fields()

        last_week_light_nutrition_reports = DailyIntakesReport.get_for_user_between_dates(
            request.user,
            from_date,
            to_date
        ).annotate_with_nutrient_totals()

        last_peritoneal_dialysis = ManualPeritonealDialysis.filter_for_user(
            request.user
        ).order_by('is_completed', '-started_at')[:3]

        not_completed_peritoneal_dialysis = ManualPeritonealDialysis.filter_for_user(request.user) \
            .filter_not_completed().first()

        return ManualPeritonealDialysisScreenResponse(
            last_week_health_statuses=weekly_health_statuses,
            last_week_light_nutrition_reports=last_week_light_nutrition_reports,
            peritoneal_dialysis_in_progress=not_completed_peritoneal_dialysis,
            last_peritoneal_dialysis=last_peritoneal_dialysis,
        )


@dataclass(frozen=True)
class DailyIntakesReportsLightResponse:
    daily_intakes_light_reports: List[DailyIntakesReport]

    @staticmethod
    def from_api_request(request: Request) -> DailyIntakesReportsLightResponse:
        date_from, date_to = parse_date_query_params(request, required=False)

        daily_intakes_reports = DailyIntakesReport.get_for_user_between_dates(request.user, date_from, date_to) \
            .annotate_with_nutrient_totals() \
            .exclude_empty_intakes()

        return DailyIntakesReportsLightResponse(
            daily_intakes_light_reports=daily_intakes_reports
        )


@dataclass(frozen=True)
class DailyIntakesReportResponse:
    daily_intakes_report: DailyIntakesReport


@dataclass(frozen=True)
class NutritionScreenV2Response:
    today_light_nutrition_report: DailyIntakesReport
    last_week_light_nutrition_reports: List[DailyIntakesReport]
    current_month_nutrition_reports: List[DailyIntakesReport]
    latest_intakes: List[Intake]
    nutrition_summary_statistics: dict

    @staticmethod
    def from_api_request(request: Request) -> NutritionScreenV2Response:
        user = request.user
        tz = utils.parse_time_zone(request)

        now = datetime.datetime.now(tz)

        month_start, month_end = utils.get_month_day_range(now.date())

        from_date = (now - datetime.timedelta(days=6)).date()
        to_date = now.date()

        DailyIntakesReport.get_or_create_for_user_and_date(user, to_date)

        last_week_light_nutrition_reports = DailyIntakesReport.get_for_user_between_dates(
            user,
            from_date,
            to_date
        ).annotate_with_nutrient_totals()

        current_month_nutrition_reports = DailyIntakesReport.get_for_user_between_dates(
            request.user,
            month_start,
            month_end
        ).annotate_with_nutrient_totals().exclude_empty_intakes()

        today_light_nutrition_report = max(last_week_light_nutrition_reports, key=lambda r: r.date)
        latest_intakes = Intake.get_latest_user_intakes(user)[:3]
        nutrition_summary_statistics = DailyIntakesReport.summarize_for_user(user)

        return NutritionScreenV2Response(
            today_light_nutrition_report=today_light_nutrition_report,
            last_week_light_nutrition_reports=last_week_light_nutrition_reports,
            latest_intakes=latest_intakes,
            nutrition_summary_statistics=nutrition_summary_statistics,
            current_month_nutrition_reports=current_month_nutrition_reports,
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
    daily_health_statuses: QuerySet[DailyHealthStatus]

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
    daily_health_statuses: QuerySet[DailyHealthStatus]

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
    def from_api_request(request: Request, limit: int) -> ProductSearchResponse:
        query = request.query_params.get('query', '')

        meal_type_str = request.query_params.get('meal_type', '').lower()

        meal_type = next(iter([e for e in MealType.values if str(e).lower() == meal_type_str]), MealType.Unknown)

        exclude_product_str_ids = request.query_params.get('exclude_products', '').split(',')
        exclude_product_ids = list(
            filter(
                lambda i: i is not None,
                [utils.try_parse_int(x) for x in exclude_product_str_ids]
            )
        )
        user = request.user

        products = Product.filter_by_user_and_query(user, query, exclude_product_ids)[:limit]
        daily_nutrient_norms_and_totals = DailyIntakesReport.get_latest_daily_nutrient_norms_and_totals(user)

        if query:
            submit_str = request.query_params.get('submit', None)
            excluded_products_count = len(exclude_product_ids)

            submit = None
            if submit_str in ('0', 'false'):
                submit = False
            elif submit_str in ('1', 'true'):
                submit = True

            ProductSearchLog.insert_from_product_search(query, products, user, submit, excluded_products_count,
                                                        meal_type)

        return ProductSearchResponse(
            products=products,
            query=query,
            daily_nutrient_norms_and_totals=daily_nutrient_norms_and_totals,
        )


@dataclass(frozen=True)
class GeneralRecommendationsResponse:
    read_recommendation_ids: List[int]
    categories: QuerySet[GeneralRecommendationCategory]
