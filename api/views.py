import datetime

from django.db.models import QuerySet
from django.http import Http404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.generics import CreateAPIView, DestroyAPIView, ListAPIView, RetrieveAPIView, RetrieveUpdateAPIView, \
    RetrieveUpdateDestroyAPIView, UpdateAPIView, get_object_or_404

from api import serializers
from api.models import HealthStatusScreenResponse, HealthStatusWeeklyResponse, NutrientScreenResponse, \
    NutrientWeeklyScreenResponse
from api.utils import datetime_to_date, parse_date_or_validation_error, parse_time_zone
from core import models


@extend_schema(
    tags=['nutrition'],
    parameters=[
        OpenApiParameter(
            name='query',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
        )
    ],
)
class ProductListView(ListAPIView):
    queryset = models.Product.objects.all()
    serializer_class = serializers.ProductSerializer
    _limit = 20

    def get_queryset(self):
        query = self.request.query_params.get('query', None)

        return models.Product.filter_by_user_and_query(self.request.user, query, self._limit)


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
class NutritionScreenView(RetrieveAPIView):
    serializer_class = serializers.NutrientScreenResponseSerializer

    def get_object(self) -> NutrientScreenResponse:
        return NutrientScreenResponse.from_api_request(self.request)


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
