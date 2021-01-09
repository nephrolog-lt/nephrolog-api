from logging import getLogger

from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from core.models import DailyHealthStatus, DailyIntakesReport, Intake, Product, UserProfile

logger = getLogger()


class ReadOnlySerializer(serializers.Serializer):

    def __init__(self, **kwargs):
        kwargs['read_only'] = True

        super().__init__(**kwargs)

    def update(self, instance, validated_data):
        raise RuntimeError("ReadOnlySerializer can not perform update")

    def create(self, validated_data):
        raise RuntimeError("ReadOnlySerializer can not perform create")


class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = UserProfile
        fields = ('user', 'gender', 'birthday', 'height_cm', 'weight_kg',
                  'chronic_kidney_disease_years', 'chronic_kidney_disease_stage', 'dialysis_type',
                  'diabetes_type', 'diabetes_years', 'diabetes_complications',)


class ProductSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='name_lt')

    class Meta:
        model = Product
        fields = ('id', 'name', 'product_kind',)


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
            'id', 'user', 'product_id', 'product', 'consumed_at', 'amount_g',
            'potassium_mg', 'proteins_mg', 'sodium_mg', 'phosphorus_mg', 'energy_kcal', 'liquids_ml',
        )


class DailyNutrientConsumptionSerializer(ReadOnlySerializer):
    total = serializers.IntegerField(read_only=True, min_value=0)
    norm = serializers.IntegerField(read_only=True, allow_null=True, min_value=0)

    class Meta:
        fields = ('total', 'norm')


class DailyIntakeReportSerializer(serializers.ModelSerializer):
    date = serializers.DateField(read_only=True)
    intakes = IntakeSerializer(read_only=True, many=True)

    potassium_mg = DailyNutrientConsumptionSerializer(read_only=True)
    proteins_mg = DailyNutrientConsumptionSerializer(read_only=True)
    sodium_mg = DailyNutrientConsumptionSerializer(read_only=True)
    phosphorus_mg = DailyNutrientConsumptionSerializer(read_only=True)
    energy_kcal = DailyNutrientConsumptionSerializer(read_only=True)
    liquids_ml = DailyNutrientConsumptionSerializer(read_only=True)

    class Meta:
        model = DailyIntakesReport
        fields = (
            'date', 'intakes',
            'potassium_mg', 'proteins_mg', 'sodium_mg', 'phosphorus_mg', 'energy_kcal', 'liquids_ml'
        )


class NutrientScreenResponseSerializer(ReadOnlySerializer):
    today_intakes_report = DailyIntakeReportSerializer(read_only=True)
    daily_intakes_reports = DailyIntakeReportSerializer(read_only=True, many=True)
    latest_intakes = IntakeSerializer(read_only=True, many=True)

    class Meta:
        fields = ('today_intakes_report', 'latest_intakes', 'daily_intakes',)


class NutrientWeeklyScreenResponseSerializer(ReadOnlySerializer):
    daily_intakes_reports = DailyIntakeReportSerializer(read_only=True, many=True)

    class Meta:
        fields = ('daily_intakes_reports',)


class DailyHealthStatusSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = DailyHealthStatus
        fields = (
            'date', 'user', 'systolic_blood_pressure', 'diastolic_blood_pressure', 'weight_kg', 'glucose', 'urine_ml',
            'swelling_difficulty', 'well_feeling', 'appetite', 'shortness_of_breath'
        )
        validators = (
            UniqueTogetherValidator(
                queryset=DailyHealthStatus.objects.all(),
                fields=('date', 'user')
            ),
        )


class HealthStatusScreenResponseSerializer(ReadOnlySerializer):
    daily_health_statuses = DailyHealthStatusSerializer(read_only=True, many=True)

    class Meta:
        fields = ('health_status_reports',)


class HealthStatusWeeklyScreenResponseSerializer(ReadOnlySerializer):
    daily_health_statuses = DailyHealthStatusSerializer(read_only=True, many=True)

    class Meta:
        fields = ('health_status_reports',)
