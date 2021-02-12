from logging import getLogger
from typing import Any, Dict

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from core.models import DailyHealthStatus, DailyIntakesReport, Intake, Product, Swelling, UserProfile, User

logger = getLogger()


class ReadOnlySerializer(serializers.Serializer):

    def __init__(self, *args, **kwargs):
        kwargs['read_only'] = True

        super().__init__(*args, **kwargs)

    def update(self, instance, validated_data):
        raise RuntimeError("ReadOnlySerializer can not perform update")

    def create(self, validated_data):
        raise RuntimeError("ReadOnlySerializer can not perform create")


@extend_schema_serializer(exclude_fields=['weight_kg', 'birthday'])
class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = UserProfile
        fields = ('user', 'gender', 'birthday', 'year_of_birth', 'height_cm', 'weight_kg',
                  'chronic_kidney_disease_years', 'chronic_kidney_disease_stage', 'dialysis_type',
                  'diabetes_type', 'diabetes_years', 'diabetes_complications',)


class NutritionSummaryStatisticsSerializer(ReadOnlySerializer):
    min_report_date = serializers.DateField(allow_null=True)
    max_report_date = serializers.DateField(allow_null=True)

    class Meta:
        fields = ('min_report_date', 'max_report_date')


class UserSerializer(serializers.ModelSerializer):
    nutrition_summary = NutritionSummaryStatisticsSerializer(source='nutrition_summary_statistics')

    class Meta:
        model = User
        fields = ('is_marketing_allowed', 'nutrition_summary')


class UserAppReviewSerializer(serializers.ModelSerializer):
    show_app_review_dialog = serializers.BooleanField(read_only=True, source='show_app_review_dialog_if_needed')

    class Meta:
        model = User
        fields = ('show_app_review_dialog',)


class ProductSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='name_lt')

    class Meta:
        model = Product
        fields = ('id', 'name', 'product_kind',
                  'potassium_mg', 'proteins_mg', 'sodium_mg', 'phosphorus_mg', 'energy_kcal', 'liquids_g',
                  'density_g_ml')


@extend_schema_serializer(exclude_fields=['liquids_ml'])
class IntakeSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product', write_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    potassium_mg = serializers.IntegerField(read_only=True)
    proteins_mg = serializers.IntegerField(read_only=True)
    sodium_mg = serializers.IntegerField(read_only=True)
    phosphorus_mg = serializers.IntegerField(read_only=True)
    energy_kcal = serializers.IntegerField(read_only=True)
    liquids_g = serializers.IntegerField(read_only=True)
    # TODO remove this one in the near future
    liquids_ml = serializers.IntegerField(read_only=True, source='liquids_g')

    class Meta:
        model = Intake
        fields = (
            'id', 'user', 'product_id', 'meal_type', 'consumed_at', 'amount_g', 'amount_ml',
            'potassium_mg', 'proteins_mg', 'sodium_mg', 'phosphorus_mg', 'energy_kcal', 'liquids_g', 'liquids_ml',
            'product',
        )


class DailyNutrientConsumptionSerializer(ReadOnlySerializer):
    norm = serializers.IntegerField(read_only=True, allow_null=True, min_value=1)
    total = serializers.IntegerField(read_only=True, min_value=0)

    class Meta:
        fields = ('norm', 'total')


class DailyNutrientNormsWithTotalsSerializer(ReadOnlySerializer):
    potassium_mg = DailyNutrientConsumptionSerializer(read_only=True)
    proteins_mg = DailyNutrientConsumptionSerializer(read_only=True)
    sodium_mg = DailyNutrientConsumptionSerializer(read_only=True)
    phosphorus_mg = DailyNutrientConsumptionSerializer(read_only=True)
    energy_kcal = DailyNutrientConsumptionSerializer(read_only=True)
    liquids_g = DailyNutrientConsumptionSerializer(read_only=True)

    class Meta:
        fields = ('potassium_mg', 'proteins_mg', 'sodium_mg', 'phosphorus_mg', 'energy_kcal', 'liquids_g',)


@extend_schema_serializer(
    exclude_fields=['liquids_ml', 'potassium_mg', 'proteins_mg', 'sodium_mg', 'phosphorus_mg', 'energy_kcal',
                    'liquids_g'])
class DailyIntakesReportSerializer(serializers.ModelSerializer):
    date = serializers.DateField(read_only=True)

    daily_nutrient_norms_and_totals = DailyNutrientNormsWithTotalsSerializer()

    intakes = IntakeSerializer(read_only=True, many=True)

    # Deprecated fields on 02-06
    potassium_mg = DailyNutrientConsumptionSerializer(read_only=True)
    proteins_mg = DailyNutrientConsumptionSerializer(read_only=True)
    sodium_mg = DailyNutrientConsumptionSerializer(read_only=True)
    phosphorus_mg = DailyNutrientConsumptionSerializer(read_only=True)
    energy_kcal = DailyNutrientConsumptionSerializer(read_only=True)
    liquids_g = DailyNutrientConsumptionSerializer(read_only=True)
    liquids_ml = DailyNutrientConsumptionSerializer(read_only=True)

    class Meta:
        model = DailyIntakesReport
        fields = (
            'date', 'intakes', 'daily_nutrient_norms_and_totals',
            'potassium_mg', 'proteins_mg', 'sodium_mg', 'phosphorus_mg', 'energy_kcal', 'liquids_g', 'liquids_ml',
        )


class DailyIntakesLightReportSerializer(serializers.ModelSerializer):
    date = serializers.DateField(read_only=True)
    nutrient_norms_and_totals = DailyNutrientNormsWithTotalsSerializer(source='daily_nutrient_norms_and_totals')

    class Meta:
        model = DailyIntakesReport
        fields = (
            'date', 'nutrient_norms_and_totals',
        )


class DailyIntakesReportsResponseSerializer(ReadOnlySerializer):
    daily_intakes_light_reports = DailyIntakesLightReportSerializer(read_only=True, many=True)

    class Meta:
        fields = ('daily_intakes_light_reports',)


class DailyIntakesReportResponseSerializer(ReadOnlySerializer):
    daily_intakes_report = DailyIntakesReportSerializer(source='*')

    class Meta:
        fields = ('daily_intakes_report',)


class NutritionScreenResponseSerializer(ReadOnlySerializer):
    today_intakes_report = DailyIntakesReportSerializer(read_only=True)
    daily_intakes_reports = DailyIntakesReportSerializer(read_only=True, many=True)
    latest_intakes = IntakeSerializer(read_only=True, many=True)
    current_month_daily_reports = DailyIntakesLightReportSerializer(read_only=True, many=True)
    nutrition_summary_statistics = NutritionSummaryStatisticsSerializer(read_only=True)

    class Meta:
        fields = ('today_intakes_report', 'latest_intakes', 'daily_intakes', 'current_month_daily_reports',
                  'nutrition_summary_statistics')


class NutrientWeeklyScreenResponseSerializer(ReadOnlySerializer):
    earliest_report_date = serializers.DateField(read_only=True, allow_null=True)
    daily_intakes_reports = DailyIntakesReportSerializer(read_only=True, many=True)

    class Meta:
        fields = ('earliest_report_date', 'daily_intakes_reports',)


class SwellingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Swelling
        fields = ('swelling',)


class DailyHealthStatusSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    swellings = SwellingSerializer(many=True)

    class Meta:
        model = DailyHealthStatus
        fields = (
            'date', 'user', 'systolic_blood_pressure', 'diastolic_blood_pressure', 'weight_kg', 'glucose', 'urine_ml',
            'swelling_difficulty', 'well_feeling', 'appetite', 'shortness_of_breath', 'swellings',
        )
        validators = (
            UniqueTogetherValidator(
                queryset=DailyHealthStatus.objects.all(),
                fields=('date', 'user')
            ),
        )

    def _replace_swellings(self, health_status: DailyHealthStatus, swellings_data: Dict):
        health_status.swellings.clear()
        for data in swellings_data:
            health_status.swellings.create(swelling=data['swelling'])

    def update(self, instance: DailyHealthStatus, validated_data: Dict) -> DailyHealthStatus:
        swellings_data = validated_data.pop('swellings', None)

        health_status: DailyHealthStatus = super().update(instance, validated_data)

        self._replace_swellings(health_status, swellings_data)

        return health_status

    def create(self, validated_data: Dict) -> DailyHealthStatus:
        swellings_data = validated_data.pop('swellings', None)

        health_status = super().create(validated_data)

        self._replace_swellings(health_status, swellings_data)

        return health_status


class HealthStatusScreenResponseSerializer(ReadOnlySerializer):
    has_any_statuses = serializers.BooleanField(read_only=True)
    daily_health_statuses = DailyHealthStatusSerializer(read_only=True, many=True)

    class Meta:
        fields = ('has_any_statuses', 'health_status_reports',)


class HealthStatusWeeklyScreenResponseSerializer(ReadOnlySerializer):
    earliest_health_status_date = serializers.DateField(read_only=True, allow_null=True)
    daily_health_statuses = DailyHealthStatusSerializer(read_only=True, many=True)

    class Meta:
        fields = ('earliest_health_status_date', 'health_status_reports',)


class ProductSearchResponseSerializer(serializers.Serializer):
    query = serializers.CharField(allow_blank=True)
    products = ProductSerializer(many=True)
    daily_nutrient_norms_and_totals = DailyNutrientNormsWithTotalsSerializer()

    class Meta:
        fields = ('query', 'daily_nutrient_norms_and_totals', 'products')
