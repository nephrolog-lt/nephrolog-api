from logging import getLogger
from typing import Dict

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from core.models import BloodPressure, DailyHealthStatus, DailyIntakesReport, GeneralRecommendation, \
    GeneralRecommendationCategory, Intake, ManualPeritonealDialysis, Product, Pulse, Swelling, User, UserProfile

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


# liquids_g excluded on 02-26
@extend_schema_serializer(exclude_fields=['liquids_g'])
class ProductSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='name_lt')
    liquids_ml = serializers.IntegerField()

    class Meta:
        model = Product
        fields = (
            'id',
            'name',
            'product_kind',
            'potassium_mg',
            'proteins_mg',
            'sodium_mg',
            'phosphorus_mg',
            'energy_kcal',
            'liquids_g',
            'liquids_ml',
            'carbohydrates_mg',
            'fat_mg',
            'density_g_ml'
        )


# liquids_g excluded on 02-26
@extend_schema_serializer(exclude_fields=['liquids_g'])
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
    liquids_ml = serializers.IntegerField(read_only=True)

    class Meta:
        model = Intake
        fields = (
            'id',
            'user',
            'product_id',
            'meal_type',
            'consumed_at',
            'amount_g',
            'amount_ml',
            'potassium_mg',
            'proteins_mg',
            'sodium_mg',
            'phosphorus_mg',
            'energy_kcal',
            'liquids_g',
            'liquids_ml',
            'carbohydrates_mg',
            'fat_mg',
            'product',
        )


class DailyNutrientConsumptionSerializer(ReadOnlySerializer):
    norm = serializers.IntegerField(read_only=True, allow_null=True, min_value=1)
    total = serializers.IntegerField(read_only=True, min_value=0)

    class Meta:
        fields = ('norm', 'total')


# liquids_g excluded on 02-26
@extend_schema_serializer(exclude_fields=['liquids_g'])
class DailyNutrientNormsWithTotalsSerializer(ReadOnlySerializer):
    potassium_mg = DailyNutrientConsumptionSerializer(read_only=True)
    proteins_mg = DailyNutrientConsumptionSerializer(read_only=True)
    sodium_mg = DailyNutrientConsumptionSerializer(read_only=True)
    phosphorus_mg = DailyNutrientConsumptionSerializer(read_only=True)
    energy_kcal = DailyNutrientConsumptionSerializer(read_only=True)
    liquids_g = DailyNutrientConsumptionSerializer(read_only=True)
    liquids_ml = DailyNutrientConsumptionSerializer(read_only=True)
    carbohydrates_mg = DailyNutrientConsumptionSerializer(read_only=True)
    fat_mg = DailyNutrientConsumptionSerializer(read_only=True)

    class Meta:
        fields = (
            'potassium_mg',
            'proteins_mg',
            'sodium_mg',
            'phosphorus_mg',
            'energy_kcal',
            'liquids_g',
            'liquids_ml',
            'carbohydrates_mg',
            'fat_mg',
        )


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


class NutritionScreenV2ResponseSerializer(ReadOnlySerializer):
    today_light_nutrition_report = DailyIntakesLightReportSerializer(read_only=True)
    last_week_light_nutrition_reports = DailyIntakesLightReportSerializer(read_only=True, many=True)
    current_month_nutrition_reports = DailyIntakesLightReportSerializer(read_only=True, many=True)
    latest_intakes = IntakeSerializer(read_only=True, many=True)
    nutrition_summary_statistics = NutritionSummaryStatisticsSerializer(read_only=True)

    class Meta:
        fields = ('last_week_light_nutrition_reports', 'latest_intakes', 'daily_intakes',
                  'nutrition_summary_statistics', 'current_month_nutrition_reports')


class NutrientWeeklyScreenResponseSerializer(ReadOnlySerializer):
    earliest_report_date = serializers.DateField(read_only=True, allow_null=True)
    daily_intakes_reports = DailyIntakesReportSerializer(read_only=True, many=True)

    class Meta:
        fields = ('earliest_report_date', 'daily_intakes_reports',)


class SwellingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Swelling
        fields = ('swelling',)


class BloodPressureSerializer(serializers.ModelSerializer):
    class Meta:
        model = BloodPressure
        fields = (
            'id', 'systolic_blood_pressure', 'diastolic_blood_pressure', 'measured_at',
        )

    def create(self, validated_data):
        daily_health_status = validated_data.pop('daily_health_status')
        measured_at = validated_data.pop('measured_at')

        instance, _ = BloodPressure.objects.update_or_create(
            daily_health_status=daily_health_status,
            measured_at=measured_at,
            defaults=validated_data
        )

        return instance


class PulseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pulse
        fields = (
            'id', 'pulse', 'measured_at',
        )

    def create(self, validated_data):
        daily_health_status = validated_data.pop('daily_health_status')
        measured_at = validated_data.pop('measured_at')

        instance, _ = Pulse.objects.update_or_create(
            daily_health_status=daily_health_status,
            measured_at=measured_at,
            defaults=validated_data
        )

        return instance


class ManualPeritonealDialysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManualPeritonealDialysis
        fields = (
            'id',

            'is_completed',
            'started_at',

            'dialysis_solution',
            'solution_in_ml',
            'solution_out_ml',
            'dialysate_color',

            'notes',
            'finished_at'
        )


# Excluded on 02-18 remove in the future: diastolic_blood_pressure, systolic_blood_pressure
@extend_schema_serializer(exclude_fields=['systolic_blood_pressure', 'diastolic_blood_pressure'])
class DailyHealthStatusSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    swellings = SwellingSerializer(many=True)
    blood_pressures = BloodPressureSerializer(many=True, read_only=True)
    pulses = PulseSerializer(many=True, read_only=True)
    manual_peritoneal_dialysis = ManualPeritonealDialysisSerializer(many=True, read_only=True)

    class Meta:
        model = DailyHealthStatus
        fields = (
            'date', 'user', 'systolic_blood_pressure', 'diastolic_blood_pressure', 'weight_kg', 'glucose', 'urine_ml',
            'swelling_difficulty', 'well_feeling', 'appetite', 'shortness_of_breath', 'swellings', 'blood_pressures',
            'pulses', 'manual_peritoneal_dialysis'
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

        if swellings_data is not None:
            self._replace_swellings(health_status, swellings_data)

        return health_status

    def create(self, validated_data: Dict) -> DailyHealthStatus:
        swellings_data = validated_data.pop('swellings', None) or []

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


class GeneralRecommendationSerializer(serializers.ModelSerializer):
    question = serializers.CharField(source='question_lt')
    answer = serializers.CharField(source='answer_lt')

    class Meta:
        model = GeneralRecommendation
        fields = ('id', 'question', 'answer', 'order')


class GeneralRecommendationCategorySerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='name_lt')
    recommendations = GeneralRecommendationSerializer(many=True)

    class Meta:
        model = GeneralRecommendationCategory
        fields = ('id', 'name', 'order', 'recommendations')


class GeneralRecommendationsResponseSerializer(ReadOnlySerializer):
    categories = GeneralRecommendationCategorySerializer(many=True, source='*')

    class Meta:
        fields = ('categories',)


class UserBloodPressurePrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        user = self.context['request'].user

        return BloodPressure.filter_for_user(user)


class UserPulsePrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        user = self.context['request'].user

        return Pulse.filter_for_user(user)


class ManualPeritonealDialysisLegacySerializer(serializers.ModelSerializer):
    blood_pressure_id = UserBloodPressurePrimaryKeyRelatedField(source='blood_pressure', write_only=True,
                                                                allow_null=True, required=False)
    pulse_id = UserPulsePrimaryKeyRelatedField(source='pulse', write_only=True, allow_null=True, required=False)

    blood_pressure = BloodPressureSerializer(read_only=True)
    pulse = PulseSerializer(read_only=True)

    liquids_ml = serializers.IntegerField(default=0, read_only=True)
    urine_ml = serializers.IntegerField(source='daily_health_status.urine_ml', allow_null=True, read_only=True)
    weight_kg = serializers.DecimalField(source='daily_health_status.weight_kg', allow_null=True, read_only=True,
                                         max_digits=4, decimal_places=1)

    class Meta:
        model = ManualPeritonealDialysis
        fields = (
            'id',

            'is_completed',
            'started_at',

            'blood_pressure',
            'blood_pressure_id',
            'pulse',
            'pulse_id',

            'urine_ml',
            'weight_kg',
            'liquids_ml',

            'dialysis_solution',
            'solution_in_ml',
            'solution_out_ml',
            'dialysate_color',

            'notes',
            'finished_at'
        )


class DailyManualPeritonealDialysisReportSerializer(serializers.ModelSerializer):
    manual_peritoneal_dialysis = ManualPeritonealDialysisLegacySerializer(many=True)

    class Meta:
        model = DailyHealthStatus
        fields = (
            'date',

            'manual_peritoneal_dialysis',

            'urine_ml',
            'weight_kg',
        )


class DailyManualPeritonealDialysisReportResponseSerializer(serializers.Serializer):
    manual_peritoneal_dialysis_reports = DailyManualPeritonealDialysisReportSerializer(many=True)

    class Meta:
        fields = (
            'manual_peritoneal_dialysis_reports',
        )


class ManualPeritonealDialysisLegacyScreenResponseSerializer(ReadOnlySerializer):
    peritoneal_dialysis_in_progress = ManualPeritonealDialysisLegacySerializer(allow_null=True)
    has_manual_peritoneal_dialysis = serializers.BooleanField()
    last_week_manual_dialysis_reports = DailyManualPeritonealDialysisReportSerializer(many=True)
    last_week_light_nutrition_reports = DailyIntakesLightReportSerializer(many=True)
    last_week_health_statuses = DailyHealthStatusSerializer(many=True)

    class Meta:
        fields = (
            'peritoneal_dialysis_in_progress',
            'has_manual_peritoneal_dialysis',
            'last_week_manual_dialysis_reports',
            'last_week_light_nutrition_reports',
            'last_week_health_statuses',
        )


class ManualPeritonealDialysisScreenResponseSerializer(ReadOnlySerializer):
    peritoneal_dialysis_in_progress = ManualPeritonealDialysisSerializer(allow_null=True)
    last_peritoneal_dialysis = ManualPeritonealDialysisSerializer(many=True, allow_empty=True)
    last_week_light_nutrition_reports = DailyIntakesLightReportSerializer(many=True)
    last_week_health_statuses = DailyHealthStatusSerializer(many=True)

    class Meta:
        fields = (
            'peritoneal_dialysis_in_progress',
            'last_peritoneal_dialysis',
            'last_week_light_nutrition_reports',
            'last_week_health_statuses',
        )
