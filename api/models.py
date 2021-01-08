from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import List

from django.db.models.enums import TextChoices
from rest_framework.request import Request

from api import utils
from core.models import DailyHealthStatus, DailyIntakesReport, Intake, UserProfile


class Nutrient(TextChoices):
    Unknown = "Unknown"
    Potassium = "Potassium"
    Proteins = "Proteins"
    Sodium = "Sodium"
    Phosphorus = "Phosphorus"
    Liquids = "Liquids"
    Energy = "Energy"


class HealthIndicator(TextChoices):
    Unknown = "Unknown"
    BloodPressure = "BloodPressure"
    Weight = "Weight"
    Urine = "Urine"
    SeverityOfSwelling = "SeverityOfSwelling"
    Swellings = "Swellings"
    WellBeing = "WellBeing"
    Appetite = "Appetite"
    ShortnessOfBreath = "ShortnessOfBreath"


@dataclass(frozen=True)
class NutrientScreenResponse:
    today_intakes_report: DailyIntakesReport
    latest_intakes: List[Intake]
    daily_intakes_reports: List[DailyIntakesReport]

    @staticmethod
    def from_api_request(request: Request) -> NutrientScreenResponse:
        user = request.user
        tz = utils.parse_time_zone(request)

        now = datetime.datetime.now(tz)

        from_date = (now - datetime.timedelta(days=7)).date()
        to_date = now.date()

        today_intakes_report = DailyIntakesReport.get_or_create_for_user_and_date(user, to_date)
        daily_intakes_reports = DailyIntakesReport.get_for_user_between_dates(request.user, from_date, to_date)
        latest_intakes = Intake.get_latest_user_intakes(user, 3)

        return NutrientScreenResponse(
            today_intakes_report=today_intakes_report,
            daily_intakes_reports=daily_intakes_reports,
            latest_intakes=latest_intakes
        )


@dataclass(frozen=True)
class NutrientWeeklyScreenResponse:
    daily_intakes_reports: List[DailyIntakesReport]


@dataclass(frozen=True)
class HealthStatusScreenResponse:
    daily_health_statuses: List[DailyHealthStatus]

    @staticmethod
    def from_api_request(request: Request) -> HealthStatusScreenResponse:
        user = request.user
        tz = utils.parse_time_zone(request)

        now = datetime.datetime.now(tz)

        from_date = (now - datetime.timedelta(days=7)).date()
        to_date = now.date()

        daily_health_statuses = DailyHealthStatus.get_between_dates_for_user(user, from_date, to_date)

        return HealthStatusScreenResponse(
            daily_health_statuses=daily_health_statuses
        )


@dataclass(frozen=True)
class HealthStatusWeeklyResponse:
    daily_health_statuses: List[DailyHealthStatus]
