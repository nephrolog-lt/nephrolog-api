import datetime

from django.db.models import QuerySet
from django.http import Http404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.generics import CreateAPIView, DestroyAPIView, ListAPIView, RetrieveAPIView, RetrieveUpdateAPIView, \
    RetrieveUpdateDestroyAPIView, UpdateAPIView, get_object_or_404

from api import serializers
from api.models import DailyManualPeritonealDialysisReportsResponse, HealthStatusScreenResponse, \
    HealthStatusWeeklyResponse, NutritionScreenResponse, \
    NutrientWeeklyScreenResponse, NutritionScreenV2Response, ProductSearchResponse, DailyIntakesReportsLightResponse
from api.utils import date_from_request_and_validated_data, datetime_to_date, parse_date_or_validation_error, \
    parse_time_zone
from core import models


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
            enum=models.MealType,
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


@extend_schema(
    tags=['nutrition'],
    deprecated=True,
    parameters=[
        OpenApiParameter(
            name='query',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
        ),
        OpenApiParameter(
            name='submit',
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY
        ),
    ],
)
class ProductListView(ListAPIView):
    queryset = models.Product.objects.all()
    serializer_class = serializers.ProductSerializer
    _limit = 20

    def get_queryset(self):
        query = self.request.query_params.get('query', None)

        products = models.Product.filter_by_user_and_query(self.request.user, query)[:self._limit]

        if query:
            submit_str = self.request.query_params.get('submit', None)

            submit = None
            if submit_str in ('0', 'false'):
                submit = False
            elif submit_str in ('1', 'true'):
                submit = True

            models.ProductSearchLog.insert_from_product_search(query, products, self.request.user, submit)

        return products


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
    tags=['nutrition'],
    deprecated=True,
)
class NutritionScreenView(RetrieveAPIView):
    serializer_class = serializers.NutritionScreenResponseSerializer

    def get_object(self) -> NutritionScreenResponse:
        return NutritionScreenResponse.from_api_request(self.request)


@extend_schema(
    tags=['nutrition']
)
class NutritionScreenV2View(RetrieveAPIView):
    serializer_class = serializers.NutritionScreenV2ResponseSerializer

    def get_object(self) -> NutritionScreenV2Response:
        return NutritionScreenV2Response.from_api_request(self.request)


# TODO make into required in the near future. Written 02-09
@extend_schema(
    tags=['nutrition'],
    parameters=[
        OpenApiParameter(
            name='from',
            type=OpenApiTypes.DATE,
            required=False,
            location=OpenApiParameter.QUERY,
        ),
        OpenApiParameter(
            name='to',
            type=OpenApiTypes.DATE,
            required=False,
            location=OpenApiParameter.QUERY,
        ),
    ],
)
class DailyIntakesReportsLightView(RetrieveAPIView):
    serializer_class = serializers.DailyIntakesReportsResponseSerializer

    def get_object(self) -> DailyIntakesReportsLightResponse:
        return DailyIntakesReportsLightResponse.from_api_request(self.request)


@extend_schema(
    tags=['nutrition']
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
class UserProfileView(CreateAPIView, RetrieveUpdateAPIView):
    queryset = models.UserProfile.objects.all()
    serializer_class = serializers.UserProfileSerializer

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
class DailyHealthStatusByDateView(RetrieveAPIView, DestroyAPIView):
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
class BloodPressureUpdateView(UpdateAPIView):
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
class PulseUpdateView(UpdateAPIView):
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

    def get_object(self) -> HealthStatusScreenResponse:
        return models.GeneralRecommendationCategory.objects.prefetch_related('recommendations')


@extend_schema(tags=['peritoneal-dialysis'])
class CreateManualPeritonealDialysisView(CreateAPIView):
    serializer_class = serializers.ManualPeritonealDialysisSerializer

    def perform_create(self, serializer):
        date = date_from_request_and_validated_data(self.request, serializer.validated_data, 'started_at')
        daily_health_status = models.DailyHealthStatus.get_or_create_for_user_and_date(self.request.user, date)

        serializer.save(daily_health_status=daily_health_status)


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
class ManualPeritonealDialysisReportsView(RetrieveAPIView):
    serializer_class = serializers.DailyManualPeritonealDialysisReportResponseSerializer

    def get_object(self) -> DailyManualPeritonealDialysisReportsResponse:
        return DailyManualPeritonealDialysisReportsResponse.from_api_request(self.request)


@extend_schema(tags=['peritoneal-dialysis'])
class UpdateManualPeritonealDialysisView(UpdateAPIView):
    serializer_class = serializers.ManualPeritonealDialysisSerializer
    lookup_url_kwarg = 'id'

    def get_queryset(self):
        return models.ManualPeritonealDialysis.objects.filter(daily_health_status__user=self.request.user)

    def perform_update(self, serializer):
        date = date_from_request_and_validated_data(self.request, serializer.validated_data, 'started_at')
        daily_health_status = models.DailyHealthStatus.get_or_create_for_user_and_date(self.request.user, date)

        serializer.save(daily_health_status=daily_health_status)
