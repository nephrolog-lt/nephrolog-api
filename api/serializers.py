import datetime
from logging import getLogger
from typing import Dict

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from api.utils import datetime_from_request_and_validated_data
from core.models import AutomaticPeritonealDialysis, BloodPressure, Country, DailyHealthStatus, DailyIntakesReport, \
    GeneralRecommendation, GeneralRecommendationCategory, GeneralRecommendationRead, GeneralRecommendationSubcategory, \
    Intake, ManualPeritonealDialysis, Product, Pulse, Swelling, User, UserProfile

logger = getLogger()


class ReadOnlySerializer(serializers.Serializer):

    def __init__(self, *args, **kwargs):
        kwargs['read_only'] = True

        super().__init__(*args, **kwargs)

    def update(self, instance, validated_data):
        raise RuntimeError("ReadOnlySerializer can not perform update")

    def create(self, validated_data):
        raise RuntimeError("ReadOnlySerializer can not perform create")


class ReadOnlyModelSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        kwargs['read_only'] = True

        super().__init__(*args, **kwargs)

    def update(self, instance, validated_data):
        raise RuntimeError("ReadOnlySerializer can not perform update")

    def create(self, validated_data):
        raise RuntimeError("ReadOnlySerializer can not perform create")


class CountrySerializer(ReadOnlyModelSerializer):
    class Meta:
        model = Country
        fields = (
            'name',
            'code',
            'flag_emoji',
            'order',
        )


class CountryResponseSerializer(ReadOnlySerializer):
    selected_country = CountrySerializer(allow_null=True)
    suggested_country = CountrySerializer(allow_null=True)
    countries = CountrySerializer(many=True, allow_empty=False)

    class Meta:
        fields = (
            'selected_country',
            'suggested_country',
            'countries',
        )


class UserProfileV2Serializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = UserProfile
        fields = (
            'user',
            'gender',
            'height_cm',
            'chronic_kidney_disease_age',
            'chronic_kidney_disease_stage',
            'dialysis',
            'diabetes_type',
        )


class NutritionSummaryStatisticsSerializer(ReadOnlySerializer):
    min_report_date = serializers.DateField(allow_null=True)
    max_report_date = serializers.DateField(allow_null=True)

    class Meta:
        fields = ('min_report_date', 'max_report_date')


class UserSerializer(serializers.ModelSerializer):
    nutrition_summary = NutritionSummaryStatisticsSerializer(source='nutrition_summary_statistics')
    selected_country = CountrySerializer(
        source='country',
        allow_null=True,
        read_only=True,
    )

    selected_country_code = serializers.SlugRelatedField(
        queryset=Country.objects.all(),
        source='country',
        slug_field='code',
        allow_null=True,
        write_only=True,
        required=False,
    )

    class Meta:
        model = User
        fields = ('is_marketing_allowed', 'nutrition_summary', 'selected_country', 'selected_country_code')


class UserAppReviewSerializer(serializers.ModelSerializer):
    show_app_review_dialog = serializers.BooleanField(read_only=True, source='show_app_review_dialog_if_needed')

    class Meta:
        model = User
        fields = ('show_app_review_dialog',)


class ProductSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
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
            'liquids_ml',
            'carbohydrates_mg',
            'fat_mg',
            'density_g_ml'
        )


class IntakeSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product', write_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    potassium_mg = serializers.IntegerField(read_only=True)
    proteins_mg = serializers.IntegerField(read_only=True)
    sodium_mg = serializers.IntegerField(read_only=True)
    phosphorus_mg = serializers.IntegerField(read_only=True)
    energy_kcal = serializers.IntegerField(read_only=True)
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


class DailyNutrientNormsWithTotalsSerializer(ReadOnlySerializer):
    potassium_mg = DailyNutrientConsumptionSerializer(read_only=True)
    proteins_mg = DailyNutrientConsumptionSerializer(read_only=True)
    sodium_mg = DailyNutrientConsumptionSerializer(read_only=True)
    phosphorus_mg = DailyNutrientConsumptionSerializer(read_only=True)
    energy_kcal = DailyNutrientConsumptionSerializer(read_only=True)
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
            'liquids_ml',
            'carbohydrates_mg',
            'fat_mg',
        )


class DailyIntakesReportSerializer(serializers.ModelSerializer):
    date = serializers.DateField(read_only=True)

    daily_nutrient_norms_and_totals = DailyNutrientNormsWithTotalsSerializer()

    intakes = IntakeSerializer(read_only=True, many=True)

    class Meta:
        model = DailyIntakesReport
        fields = (
            'date', 'intakes', 'daily_nutrient_norms_and_totals',
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
    finished_at = serializers.DateTimeField(allow_null=True, read_only=True)

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


class DailyHealthStatusSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    swellings = SwellingSerializer(many=True)
    blood_pressures = BloodPressureSerializer(many=True, read_only=True)
    pulses = PulseSerializer(many=True, read_only=True)
    manual_peritoneal_dialysis = ManualPeritonealDialysisSerializer(many=True, read_only=True)

    class Meta:
        model = DailyHealthStatus
        fields = (
            'date', 'user', 'weight_kg', 'glucose', 'urine_ml',
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
    name = serializers.CharField(source='name_lt')
    body = serializers.CharField(source='full_body')

    class Meta:
        model = GeneralRecommendation
        fields = ('id', 'name', 'body',)


class GeneralRecommendationSubcategorySerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='name_lt')
    recommendations = GeneralRecommendationSerializer(many=True)

    class Meta:
        model = GeneralRecommendationSubcategory
        fields = ('name', 'recommendations',)


class GeneralRecommendationCategorySerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='name_lt')
    subcategories = GeneralRecommendationSubcategorySerializer(many=True)

    class Meta:
        model = GeneralRecommendationCategory
        fields = ('name', 'subcategories',)


class GeneralRecommendationsResponseSerializer(ReadOnlySerializer):
    read_recommendation_ids = serializers.ListField(child=serializers.IntegerField())
    categories = GeneralRecommendationCategorySerializer(many=True)

    class Meta:
        fields = ('read_recommendation_ids', 'categories',)


class CreateGeneralRecommendationReadSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    general_recommendation = serializers.PrimaryKeyRelatedField(queryset=GeneralRecommendation.objects.all())

    class Meta:
        model = GeneralRecommendationRead
        fields = (
            'user',
            'general_recommendation',
        )

    def create(self, validated_data: Dict) -> DailyHealthStatus:
        general_recommendation = validated_data['general_recommendation']
        user = self.context['request'].user

        recommendation_read, _ = GeneralRecommendationRead.objects.update_or_create(
            user=user,
            general_recommendation=general_recommendation
        )

        return recommendation_read


class UserBloodPressurePrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        user = self.context['request'].user

        return BloodPressure.filter_for_user(user)


class UserPulsePrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        user = self.context['request'].user

        return Pulse.filter_for_user(user)


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


class AutomaticPeritonealDialysisSerializer(serializers.ModelSerializer):
    date = serializers.DateField(source='daily_health_status.date', read_only=True)
    daily_health_status = DailyHealthStatusSerializer(read_only=True)
    daily_intakes_light_report = DailyIntakesLightReportSerializer(source='daily_intakes_report', read_only=True)

    def validate(self, data):
        if 'finished_at' in data and data['started_at'] > data['finished_at']:
            raise serializers.ValidationError("finish must occur after start")

        if self.instance is None:
            request = self.context['request']
            dt = datetime_from_request_and_validated_data(request, data, 'started_at')
            date = (dt - datetime.timedelta(hours=3)).date()

            dialysis_exists = AutomaticPeritonealDialysis.filter_for_user_between_dates(
                request.user,
                date,
                date
            ).exists()

            if dialysis_exists:
                raise serializers.ValidationError(
                    f"Automatic peritoneal dialysis with the same date of {date} already exists"
                )

        return data

    class Meta:
        model = AutomaticPeritonealDialysis
        fields = (
            'date',

            'daily_health_status',
            'daily_intakes_light_report',

            'is_completed',
            'started_at',

            'solution_green_in_ml',
            'solution_yellow_in_ml',
            'solution_orange_in_ml',
            'solution_blue_in_ml',
            'solution_purple_in_ml',

            'initial_draining_ml',
            'total_drain_volume_ml',
            'last_fill_ml',
            'total_ultrafiltration_ml',

            'dialysate_color',
            'notes',
            'finished_at',
        )


class AutomaticPeritonealDialysisScreenResponseSerializer(ReadOnlySerializer):
    last_peritoneal_dialysis = AutomaticPeritonealDialysisSerializer(allow_null=True, read_only=True)
    last_week_health_statuses = DailyHealthStatusSerializer(many=True, read_only=True)
    last_week_light_nutrition_reports = DailyIntakesLightReportSerializer(many=True, read_only=True)
    peritoneal_dialysis_in_progress = AutomaticPeritonealDialysisSerializer(read_only=True, allow_null=True)

    class Meta:
        fields = (
            'last_peritoneal_dialysis',
            'last_week_peritoneal_dialysis',
            'last_week_light_nutrition_reports',
            'peritoneal_dialysis_in_progress'
        )


class AutomaticPeritonealDialysisPeriodResponseSerializer(ReadOnlySerializer):
    peritoneal_dialysis = AutomaticPeritonealDialysisSerializer(many=True, read_only=True)

    class Meta:
        fields = (
            'peritoneal_dialysis',
        )
