import datetime

from django.db.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView, RetrieveUpdateAPIView, \
    RetrieveUpdateDestroyAPIView, get_object_or_404

from api import serializers
from api.filters import ProductFilter
from api.mixins import OverrideSerializerDataMixin
from api.models import HealthStatusScreenResponse, HealthStatusWeeklyResponse, NutrientScreenResponse, \
    NutrientWeeklyScreenResponse
from api.utils import datetime_to_date, parse_date_query_params, parse_time_zone
from core import models
from core.models import DailyHealthStatus, DailyIntakesReport


@extend_schema(tags=['nutrition'])
class ProductListView(ListAPIView):
    queryset = models.Product.objects.all()
    serializer_class = serializers.ProductSerializer
    filterset_class = ProductFilter
    _limit = 20

    def filter_queryset(self, queryset: QuerySet[models.Product]) -> QuerySet[models.Product]:
        if not self.request.query_params.get('query', None):
            last_consumed_products = models.Product.last_consumed_products_by_user(self.request.user)[:self._limit]

            if last_consumed_products:
                return last_consumed_products

        return super().filter_queryset(queryset)[:self._limit]


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
class DailyHealthStatusView(OverrideSerializerDataMixin, RetrieveUpdateDestroyAPIView):
    queryset = models.DailyHealthStatus.objects.all()
    serializer_class = serializers.DailyHealthStatusSerializer
    lookup_field = 'date'
    lookup_url_kwarg = 'date'

    def filter_queryset(self, queryset: QuerySet[models.DailyHealthStatus]) -> QuerySet[models.DailyHealthStatus]:
        return super().filter_queryset(queryset).filter(user=self.request.user)


@extend_schema(tags=['health-status'])
class DailyHealthStatusCreateView(CreateAPIView):
    queryset = models.DailyHealthStatus.objects.all()
    serializer_class = serializers.DailyHealthStatusSerializer


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
