import datetime

from django.db.models import Prefetch, QuerySet
from django.http import Http404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.generics import CreateAPIView, DestroyAPIView, RetrieveAPIView, RetrieveUpdateAPIView, \
    RetrieveUpdateDestroyAPIView, UpdateAPIView, get_object_or_404
from rest_framework.permissions import AllowAny

from api import serializers
from api.models import AutomaticPeritonealDialysisPeriodResponse, AutomaticPeritonealDialysisScreenResponse, \
    CountryResponse, DailyIntakesReportsLightResponse, GeneralRecommendationsResponse, HealthStatusScreenResponse, \
    HealthStatusWeeklyResponse, ManualPeritonealDialysisScreenResponse, NutrientWeeklyScreenResponse, \
    NutritionScreenV2Response, ProductSearchResponse
from api.utils import date_from_request_and_validated_data, datetime_from_request_and_validated_data, datetime_to_date, \
    parse_date_or_validation_error, \
    parse_time_zone
from core import models


@extend_schema(tags=['user'])
class CountriesView(RetrieveAPIView):
    permission_classes = [AllowAny]

    serializer_class = serializers.CountryResponseSerializer

    def get_object(self) -> CountryResponse:
        return CountryResponse.from_api_request(self.request)


@extend_schema(
    tags=['nutrition'],
    parameters=[
        OpenApiParameter(
            name='query',
            type=OpenApiTypes.STR,
            default='',
            location=OpenApiParameter.QUERY,
        ),
        OpenApiParameter(
            name='submit',
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            name='meal_type',
            enum=models.MealType.values,
            default=models.MealType.Unknown,
            location=OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            name='exclude_products',
            location=OpenApiParameter.QUERY
        ),
    ],
)
class ProductSearchView(RetrieveAPIView):
    serializer_class = serializers.ProductSearchResponseSerializer
    _limit = 30

    def get_object(self):
        return ProductSearchResponse.from_api_request(self.request, self._limit)


@extend_schema(tags=['nutrition'])
class MissingProductCreateView(CreateAPIView):
    queryset = models.MissingProduct.objects.all()
    serializer_class = serializers.MissingProductSerializer


@extend_schema(tags=['nutrition'])
class IntakeView(RetrieveUpdateDestroyAPIView):
    queryset = models.Intake.objects.all()
    serializer_class = serializers.IntakeSerializer
    lookup_url_kwarg = 'id'

    def perform_update(self, serializer):
        consumed_at: datetime.datetime = serializer.validated_data['consumed_at']
        tz = parse_time_zone(self.request)
        date = datetime_to_date(consumed_at, tz)

        daily_report = models.DailyIntakesReport.get_or_create_for_user_and_date(self.request.user, date)

        serializer.save(daily_report=daily_report)


@extend_schema(tags=['nutrition'])
class IntakeCreateView(CreateAPIView):
    queryset = models.Intake.objects.all()
    serializer_class = serializers.IntakeSerializer

    def perform_create(self, serializer):
        consumed_at: datetime.datetime = serializer.validated_data['consumed_at']
        tz = parse_time_zone(self.request)
        date = datetime_to_date(consumed_at, tz)

        daily_report = models.DailyIntakesReport.get_or_create_for_user_and_date(self.request.user, date)

        serializer.save(daily_report=daily_report)


@extend_schema(
    tags=['nutrition']
)
class NutritionScreenV2View(RetrieveAPIView):
    serializer_class = serializers.NutritionScreenV2ResponseSerializer

    def get_object(self) -> NutritionScreenV2Response:
        return NutritionScreenV2Response.from_api_request(self.request)


@extend_schema(
    tags=['nutrition'],
    parameters=[
        OpenApiParameter(
            name='from',
            type=OpenApiTypes.DATE,
            required=True,
            location=OpenApiParameter.QUERY,
        ),
        OpenApiParameter(
            name='to',
            type=OpenApiTypes.DATE,
            required=True,
            location=OpenApiParameter.QUERY,
        ),
    ],
)
class DailyIntakesReportsLightView(RetrieveAPIView):
    serializer_class = serializers.DailyIntakesReportsResponseSerializer

    def get_object(self) -> DailyIntakesReportsLightResponse:
        return DailyIntakesReportsLightResponse.from_api_request(self.request)


@extend_schema(
    tags=['nutrition'],
    parameters=[
        OpenApiParameter(
            name='date',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.PATH,
        ),
    ],
)
class DailyIntakesReportView(RetrieveAPIView):
    serializer_class = serializers.DailyIntakesReportResponseSerializer
    lookup_field = 'date'

    def get_queryset(self):
        return models.DailyIntakesReport.filter_for_user(self.request.user).prefetch_intakes()


@extend_schema(
    tags=['nutrition'],
    parameters=[
        OpenApiParameter(
            name='from',
            type=OpenApiTypes.DATE,
            required=True,
            location=OpenApiParameter.QUERY,
        ),
        OpenApiParameter(
            name='to',
            type=OpenApiTypes.DATE,
            required=True,
            location=OpenApiParameter.QUERY,
        ),
    ],
)
class NutritionWeeklyScreenView(RetrieveAPIView):
    serializer_class = serializers.NutrientWeeklyScreenResponseSerializer

    def get_object(self) -> NutrientWeeklyScreenResponse:
        return NutrientWeeklyScreenResponse.from_api_request(self.request)


@extend_schema(tags=['user'])
class UserProfileV2View(CreateAPIView, RetrieveUpdateAPIView):
    queryset = models.UserProfile.objects.all()
    serializer_class = serializers.UserProfileV2Serializer

    def get_object(self):
        return get_object_or_404(self.filter_queryset(self.get_queryset()), user=self.request.user)


@extend_schema(tags=['user'])
class UserView(RetrieveAPIView, UpdateAPIView):
    serializer_class = serializers.UserSerializer

    def get_object(self):
        return models.User.objects.filter(pk=self.request.user.pk).get()


@extend_schema(tags=['user'])
class UserAppReview(RetrieveAPIView):
    serializer_class = serializers.UserAppReviewSerializer

    def get_object(self):
        return models.User.objects.get(pk=self.request.user.pk)


@extend_schema(
    tags=['health-status'],
    parameters=[
        OpenApiParameter(
            name='date',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.PATH,
        ),
    ],
)
class DailyHealthStatusByDateView(RetrieveAPIView):
    queryset = models.DailyHealthStatus.objects.all()
    serializer_class = serializers.DailyHealthStatusSerializer
    lookup_field = 'date'
    lookup_url_kwarg = 'date'

    def filter_queryset(self, queryset: QuerySet[models.DailyHealthStatus]) -> QuerySet[models.DailyHealthStatus]:
        return super().filter_queryset(queryset).filter(user=self.request.user)


@extend_schema(tags=['health-status'])
class DailyHealthStatusView(CreateAPIView, UpdateAPIView):
    serializer_class = serializers.DailyHealthStatusSerializer

    def get_object(self):
        date = parse_date_or_validation_error(self.request.data.get('date', None))

        health_status = models.DailyHealthStatus.get_for_user_and_date(self.request.user, date)
        if health_status is None:
            raise Http404

        return health_status


@extend_schema(tags=['health-status'])
class BloodPressureCreateView(CreateAPIView):
    serializer_class = serializers.BloodPressureSerializer

    def perform_create(self, serializer):
        date = date_from_request_and_validated_data(self.request, serializer.validated_data, 'measured_at')
        daily_health_status = models.DailyHealthStatus.get_or_create_for_user_and_date(self.request.user, date)

        serializer.save(daily_health_status=daily_health_status)


@extend_schema(tags=['health-status'])
class BloodPressureUpdateView(UpdateAPIView, DestroyAPIView):
    serializer_class = serializers.BloodPressureSerializer
    lookup_url_kwarg = 'id'

    def perform_update(self, serializer):
        date = date_from_request_and_validated_data(self.request, serializer.validated_data, 'measured_at')
        daily_health_status = models.DailyHealthStatus.get_or_create_for_user_and_date(self.request.user, date)

        serializer.save(daily_health_status=daily_health_status)

    def get_queryset(self):
        return models.BloodPressure.objects.filter(daily_health_status__user=self.request.user)


@extend_schema(tags=['health-status'])
class PulseCreateView(CreateAPIView):
    serializer_class = serializers.PulseSerializer

    def perform_create(self, serializer):
        date = date_from_request_and_validated_data(self.request, serializer.validated_data, 'measured_at')
        daily_health_status = models.DailyHealthStatus.get_or_create_for_user_and_date(self.request.user, date)

        serializer.save(daily_health_status=daily_health_status)


@extend_schema(tags=['health-status'])
class PulseUpdateView(UpdateAPIView, DestroyAPIView):
    serializer_class = serializers.PulseSerializer
    lookup_url_kwarg = 'id'

    def perform_update(self, serializer):
        date = date_from_request_and_validated_data(self.request, serializer.validated_data, 'measured_at')
        daily_health_status = models.DailyHealthStatus.get_or_create_for_user_and_date(self.request.user, date)

        serializer.save(daily_health_status=daily_health_status)

    def get_queryset(self):
        return models.Pulse.objects.filter(daily_health_status__user=self.request.user)


@extend_schema(tags=['health-status'])
class HealthStatusScreenView(RetrieveAPIView):
    serializer_class = serializers.HealthStatusScreenResponseSerializer

    def get_object(self) -> HealthStatusScreenResponse:
        return HealthStatusScreenResponse.from_api_request(self.request)


@extend_schema(
    tags=['health-status'],
    parameters=[
        OpenApiParameter(
            name='from',
            type=OpenApiTypes.DATE,
            required=True,
            location=OpenApiParameter.QUERY,
        ),
        OpenApiParameter(
            name='to',
            type=OpenApiTypes.DATE,
            required=True,
            location=OpenApiParameter.QUERY,
        ),
    ],
)
class HealthStatusWeeklyScreenView(RetrieveAPIView):
    serializer_class = serializers.HealthStatusWeeklyScreenResponseSerializer

    def get_object(self) -> HealthStatusWeeklyResponse:
        return HealthStatusWeeklyResponse.from_api_request(self.request)


@extend_schema(tags=['general-recommendations'])
class GeneralRecommendationsView(RetrieveAPIView):
    serializer_class = serializers.GeneralRecommendationsResponseSerializer

    def get_object(self):
        # noinspection PyUnresolvedReferences
        region = self.request.user.region_with_default

        name_filter = {f'name_{region.lower()}__isnull': False}

        categories = models.GeneralRecommendationCategory.objects.prefetch_related(
            Prefetch(
                'subcategories',
                models.GeneralRecommendationSubcategory.objects.filter(**name_filter).prefetch_related(
                    Prefetch(
                        'recommendations',
                        models.GeneralRecommendation.objects.filter(**name_filter)
                    )
                )
            )
        )

        read_recommendation_ids = models.GeneralRecommendationRead.objects.filter(
            user=self.request.user).values_list('general_recommendation', flat=True).order_by('general_recommendation')

        return GeneralRecommendationsResponse(categories=categories, read_recommendation_ids=read_recommendation_ids)


@extend_schema(tags=['general-recommendations'])
class CreateGeneralRecommendationReadView(CreateAPIView):
    serializer_class = serializers.CreateGeneralRecommendationReadSerializer


@extend_schema(tags=['peritoneal-dialysis'])
class CreateManualPeritonealDialysisView(CreateAPIView):
    serializer_class = serializers.ManualPeritonealDialysisSerializer

    def perform_create(self, serializer):
        date = date_from_request_and_validated_data(self.request, serializer.validated_data, 'started_at')
        daily_health_status = models.DailyHealthStatus.get_or_create_for_user_and_date(self.request.user, date)
        daily_intakes_report = models.DailyIntakesReport.get_or_create_for_user_and_date(self.request.user, date)

        serializer.save(daily_health_status=daily_health_status, daily_intakes_report=daily_intakes_report)


@extend_schema(tags=['peritoneal-dialysis'])
class UpdateManualPeritonealDialysisView(UpdateAPIView, DestroyAPIView):
    serializer_class = serializers.ManualPeritonealDialysisSerializer
    lookup_url_kwarg = 'id'

    def get_queryset(self):
        return models.ManualPeritonealDialysis.objects.filter(daily_health_status__user=self.request.user)

    def perform_update(self, serializer):
        date = date_from_request_and_validated_data(self.request, serializer.validated_data, 'started_at')
        daily_health_status = models.DailyHealthStatus.get_or_create_for_user_and_date(self.request.user, date)
        daily_intakes_report = models.DailyIntakesReport.get_or_create_for_user_and_date(self.request.user, date)

        serializer.save(daily_health_status=daily_health_status, daily_intakes_report=daily_intakes_report)


@extend_schema(tags=['peritoneal-dialysis'], )
class ManualPeritonealDialysisScreenView(RetrieveAPIView):
    serializer_class = serializers.ManualPeritonealDialysisScreenResponseSerializer

    def get_object(self) -> ManualPeritonealDialysisScreenResponse:
        return ManualPeritonealDialysisScreenResponse.from_api_request(self.request)


@extend_schema(tags=['peritoneal-dialysis'])
class CreateAutomaticPeritonealDialysisView(CreateAPIView):
    serializer_class = serializers.AutomaticPeritonealDialysisSerializer

    def perform_create(self, serializer):
        dt = datetime_from_request_and_validated_data(self.request, serializer.validated_data, 'started_at')
        date = (dt - datetime.timedelta(hours=3)).date()

        daily_health_status = models.DailyHealthStatus.get_or_create_for_user_and_date(self.request.user, date)
        daily_intakes_report = models.DailyIntakesReport.get_or_create_for_user_and_date(self.request.user, date)

        serializer.save(daily_health_status=daily_health_status, daily_intakes_report=daily_intakes_report)


@extend_schema(
    tags=['peritoneal-dialysis'],
    parameters=[
        OpenApiParameter(
            name='date',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.PATH,
        ),
    ],
)
class UpdateAutomaticPeritonealDialysisView(UpdateAPIView, DestroyAPIView):
    serializer_class = serializers.AutomaticPeritonealDialysisSerializer
    lookup_url_kwarg = 'date'
    lookup_field = 'daily_health_status__date'

    def get_queryset(self):
        return models.AutomaticPeritonealDialysis.objects.filter(daily_health_status__user=self.request.user)

    def perform_update(self, serializer):
        dt = datetime_from_request_and_validated_data(self.request, serializer.validated_data, 'started_at')
        date = (dt - datetime.timedelta(hours=3)).date()

        daily_health_status = models.DailyHealthStatus.get_or_create_for_user_and_date(self.request.user, date)
        daily_intakes_report = models.DailyIntakesReport.get_or_create_for_user_and_date(self.request.user, date)

        serializer.save(daily_health_status=daily_health_status, daily_intakes_report=daily_intakes_report)


@extend_schema(tags=['peritoneal-dialysis'], )
class AutomaticPeritonealDialysisScreenView(RetrieveAPIView):
    serializer_class = serializers.AutomaticPeritonealDialysisScreenResponseSerializer

    def get_object(self) -> AutomaticPeritonealDialysisScreenResponse:
        return AutomaticPeritonealDialysisScreenResponse.from_api_request(self.request)


@extend_schema(
    tags=['peritoneal-dialysis'],
    parameters=[
        OpenApiParameter(
            name='from',
            type=OpenApiTypes.DATE,
            required=True,
            location=OpenApiParameter.QUERY,
        ),
        OpenApiParameter(
            name='to',
            type=OpenApiTypes.DATE,
            required=True,
            location=OpenApiParameter.QUERY,
        ),
    ],
)
class AutomaticPeritonealDialysisPeriodView(RetrieveAPIView):
    serializer_class = serializers.AutomaticPeritonealDialysisPeriodResponseSerializer

    def get_object(self) -> AutomaticPeritonealDialysisPeriodResponse:
        return AutomaticPeritonealDialysisPeriodResponse.from_api_request(self.request)
