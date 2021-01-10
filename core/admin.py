from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from core import models


@admin.register(models.User)
class UserAdmin(BaseUserAdmin):
    pass


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name_lt',
        'name_en',
        'product_kind',
        'potassium_mg',
        'proteins_mg',
        'sodium_mg',
        'phosphorus_mg',
        'energy_kcal',
        'liquids_ml',
        'raw_id',
        'created_at',
        'updated_at',
    )
    list_filter = ('product_kind', 'created_at', 'updated_at')
    search_fields = ('name_lt', 'name_en')


class BaseUserProfileAdminMixin(admin.ModelAdmin):
    raw_id_fields = ('user',)
    list_select_related = ('user',)
    date_hierarchy = 'created_at'


@admin.register(models.HistoricalUserProfile)
class HistoricalUserProfileAdmin(BaseUserProfileAdminMixin):
    list_display = (
        'id',
        'user',
        'date',
        'gender',
        'birthday',
        'height_cm',
        'weight_kg',

        'created_at',
        'updated_at',
    )
    list_filter = ('date',)
    date_hierarchy = 'date'


@admin.register(models.UserProfile)
class UserProfileAdmin(BaseUserProfileAdminMixin):
    list_display = (
        'id',
        'user',
        'gender',
        'birthday',
        'height_cm',
        'weight_kg',

        'created_at',
        'updated_at',
    )


@admin.register(models.Intake)
class IntakeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'product',
        'consumed_at',
        'amount_g',
        'created_at',
        'updated_at',
    )
    list_select_related = ('user', 'product', 'daily_report')
    raw_id_fields = ('product', 'user', 'daily_report')
    date_hierarchy = 'consumed_at'


@admin.register(models.DailyHealthStatus)
class DailyHealthStatusAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'date',
        'systolic_blood_pressure',
        'diastolic_blood_pressure',
        'weight_kg',
        'urine_ml',
        'created_at',
        'updated_at',
    )
    date_hierarchy = 'date'


@admin.register(models.DailyIntakesReport)
class DailyIntakesReportAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'date',
        'daily_norm_potassium_mg',
        'daily_norm_proteins_mg',
        'daily_norm_sodium_mg',
        'daily_norm_phosphorus_mg',
        'daily_norm_energy_kcal',
        'daily_norm_liquids_ml',
        'created_at',
        'updated_at',
    )
    list_select_related = ('user',)
    date_hierarchy = 'date'
    raw_id_fields = ('user',)
