from csv_export.views import CSVExportView
from django.contrib import admin
from django.contrib.admin import EmptyFieldListFilter
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.postgres.search import TrigramSimilarity
from django.utils.safestring import mark_safe

from core import models
from core.models import Product

admin.site.site_header = 'NephroGo Administration'
admin.site.site_title = admin.site.site_header


@admin.register(models.User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff',
                    'profile_count',
                    'intakes_count', 'daily_intakes_reports_count',
                    'daily_health_statuses_count',
                    'historical_profiles_count',
                    'last_login', 'date_joined')

    ordering = ('last_login',)
    date_hierarchy = 'last_login'
    list_filter = (('profile', EmptyFieldListFilter),
                   'last_login', 'date_joined', 'is_staff', 'is_superuser', 'is_active',)

    def get_queryset(self, request):
        return models.User.get_annotated_with_statistics()

    def intakes_count(self, obj):
        return obj.intakes_count

    intakes_count.admin_order_field = "intakes_count"
    intakes_count.short_description = "intakes"

    def daily_intakes_reports_count(self, obj):
        return obj.daily_intakes_reports_count

    daily_intakes_reports_count.admin_order_field = "daily_intakes_reports_count"
    daily_intakes_reports_count.short_description = "daily intakes reports"

    def profile_count(self, obj):
        return obj.profile_count

    profile_count.admin_order_field = "profile_count"
    profile_count.short_description = "has profile"
    profile_count.boolean = True

    def historical_profiles_count(self, obj):
        return obj.historical_profiles_count

    historical_profiles_count.admin_order_field = "historical_profiles_count"
    historical_profiles_count.short_description = "Historical profiles"

    def daily_health_statuses_count(self, obj):
        return obj.daily_health_statuses_count

    daily_health_statuses_count.admin_order_field = "daily_health_statuses_count"
    daily_health_statuses_count.short_description = "Daily health statuses"


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'product_kind',
        'name_lt',
        'name_en',
        'most_similar',
        'density_g_ml',
        'potassium_mg',
        'proteins_mg',
        'sodium_mg',
        'phosphorus_mg',
        'energy_kcal',
        'liquids_g',
        'product_source',
        'raw_id',
        'created_at',
        'updated_at',
    )
    readonly_fields = ('product_source', 'name_search_lt',)
    list_filter = (('density_g_ml', EmptyFieldListFilter), 'product_kind', 'product_source', 'created_at', 'updated_at')
    list_editable = ('product_kind', 'name_lt', 'name_en', 'density_g_ml')
    search_fields = ('name_lt', 'name_en', 'name_search_lt')

    def most_similar(self, obj):
        return mark_safe('<br><br>'.join(map(lambda x: x.name_lt, Product.objects.annotate(
            similarity=TrigramSimilarity('name_search_lt', obj.name_search_lt)).exclude(
            pk=obj.pk).order_by('-similarity')[:3]))
                         )


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
    raw_id_fields = ('user',)
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
        'daily_norm_liquids_g',
        'created_at',
        'updated_at',
    )
    list_select_related = ('user',)
    date_hierarchy = 'date'
    raw_id_fields = ('user',)

    actions = ('export_data_csv',)

    def export_data_csv(self, request, queryset):
        view = CSVExportView(queryset=queryset.annotate_with_nutrient_totals(),
                             fields='__all__')
        return view.get(request)

    export_data_csv.short_description = 'Export CSV'
