from admin_numeric_filter.admin import NumericFilterModelAdmin, RangeNumericFilter
from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin
from csv_export.views import CSVExportView
from django.contrib import admin
from django.contrib.admin import EmptyFieldListFilter
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from core import models

admin.site.site_header = 'NephroGo Administration'
admin.site.site_title = admin.site.site_header


class UserProfileAdminInline(admin.StackedInline):
    model = models.UserProfile
    extra = 0


@admin.register(models.User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username', 'id', 'email', 'first_name', 'last_name', 'is_marketing_allowed', 'last_app_review_dialog_showed',
        'is_staff',
        'profile_count',
        'intakes_count', 'daily_intakes_reports_count',
        'daily_health_statuses_count',
        'historical_profiles_count',
        'last_login', 'date_joined')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('NephroGo info'), {'fields': ('is_marketing_allowed', 'last_app_review_dialog_showed',)}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    inlines = (UserProfileAdminInline,)

    ordering = ('-last_login',)
    search_fields = ('username', 'first_name', 'last_name', 'email', 'pk')

    date_hierarchy = 'last_login'
    list_filter = (('profile', EmptyFieldListFilter), 'is_marketing_allowed',
                   'last_login', 'date_joined', 'last_app_review_dialog_showed', 'is_staff', 'is_superuser',
                   'is_active',)

    # noinspection PyUnresolvedReferences
    def get_queryset(self, request):
        return super().get_queryset(request).annotate_with_statistics()

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


@admin.register(models.ProductSearchLog)
class ProductSearchLogAdmin(NumericFilterModelAdmin):
    list_display = (
        'query',
        'results_count',
        'product1',
        'product2',
        'product3',
        'excluded_products_count',
        'submit',
        'meal_type',
        'user',
        'created_at',
    )
    list_select_related = ('user', 'product1', 'product2', 'product3')
    list_filter = (
        'submit',
        ('results_count', RangeNumericFilter),
        ('excluded_products_count', RangeNumericFilter),
        'meal_type',
        'created_at'
    )
    search_fields = ('product1__name_lt', 'product2__name_lt', 'product3__name_lt', 'user__email', 'user__username')
    date_hierarchy = 'created_at'


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'product_kind',
        'name_lt',
        'name_en',
        'popularity',
        'density_g_ml',
        'potassium_mg',
        'proteins_mg',
        'sodium_mg',
        'phosphorus_mg',

        'carbohydrates_mg',
        'fat_mg',

        'energy_kcal',
        'liquids_g',
        'liquids_ml',

        'product_source',
        'raw_id',
        'created_at',
        'updated_at',
    )
    readonly_fields = ('product_source', 'name_search_lt',)
    list_filter = (
        ('density_g_ml', EmptyFieldListFilter),
        'product_kind',
        'product_source',
        'created_at',
        'updated_at'
    )
    search_fields = ('name_lt', 'name_en', 'name_search_lt')

    def get_queryset(self, request):
        # noinspection PyUnresolvedReferences
        return super().get_queryset(request).annotate_with_popularity()

    def popularity(self, obj):
        return obj.popularity

    popularity.admin_order_field = "popularity"
    popularity.short_description = "popularity"

    # noinspection PyMethodMayBeStatic
    def liquids_ml(self, obj):
        return obj.liquids_ml

    # def most_similar(self, obj):
    #     return mark_safe('<br><br>'.join(map(lambda x: x.name_lt, Product.objects.annotate(
    #         similarity=TrigramSimilarity('name_search_lt', obj.name_search_lt)).exclude(
    #         pk=obj.pk).order_by('-similarity')[:3]))
    #                      )


class BaseUserProfileAdminMixin(NumericFilterModelAdmin):
    raw_id_fields = ('user',)
    list_select_related = ('user',)
    search_fields = ('user__pk', 'user__email', 'user__username')
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
    list_select_related = ('user',)
    date_hierarchy = 'date'


@admin.register(models.UserProfile)
class UserProfileAdmin(BaseUserProfileAdminMixin):
    list_display = (
        'user',
        'gender',
        'year_of_birth',
        'birthday',
        'height_cm',
        'weight_kg',

        'chronic_kidney_disease_years',
        'chronic_kidney_disease_stage',
        'dialysis_type',
        'periotonic_dialysis_type',
        'diabetes_years',
        'diabetes_type',
        'diabetes_complications',

        'created_at',
        'updated_at',
    )

    list_filter = (
        'gender',
        ('year_of_birth', RangeNumericFilter),
        ('height_cm', RangeNumericFilter),
        ('weight_kg', RangeNumericFilter),
        ('chronic_kidney_disease_years', RangeNumericFilter),
        'chronic_kidney_disease_stage',
        'dialysis_type',
        'periotonic_dialysis_type',
        ('diabetes_years', RangeNumericFilter),
        'diabetes_type', 'diabetes_complications',
        'created_at',
    )


@admin.register(models.Intake)
class IntakeAdmin(admin.ModelAdmin):
    list_display = (
        'product',
        'user',
        'meal_type',
        'consumed_at',
        'amount_g',
        'amount_ml',
        'id',
        'created_at',
        'updated_at',
    )
    list_select_related = ('user', 'product')
    raw_id_fields = ('product', 'user', 'daily_report')
    search_fields = ('user__pk', 'user__email', 'user__username', 'product__name_lt')
    list_filter = ('consumed_at', 'meal_type')
    date_hierarchy = 'consumed_at'


@admin.register(models.BloodPressure)
class BloodPressureAdmin(admin.ModelAdmin):
    list_display = (
        'id',

        'systolic_blood_pressure',
        'diastolic_blood_pressure',
        'measured_at',

        'user',

        'created_at',
        'updated_at',
    )
    raw_id_fields = ('daily_health_status',)
    date_hierarchy = 'measured_at'
    list_filter = ('measured_at',)
    list_select_related = ('daily_health_status', 'daily_health_status__user')
    search_fields = (
        'daily_health_status__user__pk',
        'daily_health_status__user__email',
        'daily_health_status__user__username',
    )

    def user(self, obj):
        return str(obj.daily_health_status.user)


@admin.register(models.Pulse)
class BloodPressureAdmin(admin.ModelAdmin):
    list_display = (
        'id',

        'pulse',
        'measured_at',

        'user',

        'created_at',
        'updated_at',
    )
    raw_id_fields = ('daily_health_status',)
    date_hierarchy = 'measured_at'
    list_filter = ('measured_at',)
    list_select_related = ('daily_health_status', 'daily_health_status__user')
    search_fields = (
        'daily_health_status__user__pk',
        'daily_health_status__user__email',
        'daily_health_status__user__username',
    )

    def user(self, obj):
        return str(obj.daily_health_status.user)


class BloodPressureAdminInline(admin.StackedInline):
    model = models.BloodPressure


class PulseAdminInline(admin.StackedInline):
    model = models.Pulse


@admin.register(models.DailyHealthStatus)
class DailyHealthStatusAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'date',

        'systolic_blood_pressure',
        'diastolic_blood_pressure',
        'blood_pressures',
        'pulses',

        'weight_kg',
        'glucose',
        'urine_ml',
        'all_swellings',
        'swelling_difficulty',
        'well_feeling',
        'appetite',
        'shortness_of_breath',

        'created_at',
        'updated_at',
    )
    raw_id_fields = ('user',)
    date_hierarchy = 'date'
    list_select_related = ('user',)
    search_fields = ('user__pk', 'user__email', 'user__username',)
    inlines = (BloodPressureAdminInline, PulseAdminInline)
    list_filter = (('systolic_blood_pressure', EmptyFieldListFilter),)

    def get_queryset(self, request):
        # noinspection PyUnresolvedReferences
        return super().get_queryset(request).prefetch_all_related_fields()

    def all_swellings(self, obj):
        return ','.join(map(lambda s: str(s), obj.swellings.all()))

    all_swellings.short_description = "swellings"

    def blood_pressures(self, obj):
        html = '<br>'.join(
            map(
                lambda x: f"{x.systolic_blood_pressure}/{x.diastolic_blood_pressure}",
                obj.blood_pressures.all()
            )
        )
        return format_html(html)

    def pulses(self, obj):
        html = '<br>'.join(
            map(
                lambda x: f"{x.pulse}",
                obj.pulses.all()
            )
        )
        return format_html(html)


class IntakeAdminInline(admin.StackedInline):
    model = models.Intake
    extra = 0
    raw_id_fields = ('product', 'user',)
    ordering = ('-consumed_at',)


@admin.register(models.DailyIntakesReport)
class DailyIntakesReportAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'date',
        'intakes_count',
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
    search_fields = ('user__pk', 'user__email', 'user__username',)
    inlines = (IntakeAdminInline,)
    actions = ('export_data_csv',)

    def get_queryset(self, request):
        # noinspection PyUnresolvedReferences
        return super().get_queryset(request).annotate_with_intakes_count()

    def intakes_count(self, obj):
        return obj.intakes_count

    intakes_count.admin_order_field = "intakes_count"
    intakes_count.short_description = "intakes_count"

    def export_data_csv(self, request, queryset):
        view = CSVExportView(queryset=queryset.annotate_with_nutrient_totals(),
                             fields='__all__')
        return view.get(request)

    export_data_csv.short_description = 'Export CSV'


class GeneralRecommendationsDeprecatedInline(SortableInlineAdminMixin, admin.StackedInline):
    model = models.GeneralRecommendationDeprecated
    readonly_fields = (
        'created_at',
        'updated_at',
    )


@admin.register(models.GeneralRecommendationDeprecatedCategory)
class GeneralRecommendationCategoryDeprecatedAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = (
        'name_lt',
        'created_at',
        'updated_at',
    )
    search_fields = ('name_lt', 'questions__question_lt',)
    inlines = (GeneralRecommendationsDeprecatedInline,)


class GeneralRecommendationsSubcategoryInline(SortableInlineAdminMixin, admin.StackedInline):
    model = models.GeneralRecommendationSubcategory
    readonly_fields = (
        'created_at',
        'updated_at',
    )


@admin.register(models.GeneralRecommendationCategory)
class GeneralRecommendationCategoryAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = (
        'name_lt',
        'created_at',
        'updated_at',
    )
    search_fields = ('name_lt', 'questions__question_lt',)
    inlines = (GeneralRecommendationsSubcategoryInline,)


@admin.register(models.GeneralRecommendation)
class GeneralRecommendationAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = (
        'name_lt',
        'subcategory',
        'created_at',
        'updated_at',
    )
    search_fields = ('name_lt', 'body',)
    list_filter = ('subcategory',)
    list_select_related = ('subcategory',)


@admin.register(models.ManualPeritonealDialysis)
class ManualPeritonealDialysisAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'daily_health_status',
        'started_at',
        'is_completed',

        'weight_kg',
        'urine_ml',

        'dialysis_solution',
        'solution_in_ml',
        'solution_out_ml',
        'dialysate_color',

        'notes',
        'finished_at',

        'user',

        'created_at',
        'updated_at',
    )
    raw_id_fields = ('daily_health_status', 'daily_intakes_report')
    date_hierarchy = 'started_at'
    list_select_related = ('daily_health_status', 'daily_health_status__user')
    search_fields = ('user__pk', 'user__email', 'user__username',)
    list_filter = (
        'is_completed',
        ('finished_at', EmptyFieldListFilter),
        'dialysis_solution',
        'dialysate_color',
        ('notes', EmptyFieldListFilter),
    )

    def user(self, obj):
        return obj.daily_health_status.user

    def weight_kg(self, obj):
        return obj.daily_health_status.weight_kg

    weight_kg.admin_order_field = "daily_health_status__weight_kg"

    def urine_ml(self, obj):
        return obj.daily_health_status.urine_ml

    urine_ml.admin_order_field = "daily_health_status__urine_ml"


@admin.register(models.AutomaticPeritonealDialysis)
class ManualPeritonealDialysisAdmin(admin.ModelAdmin):
    list_display = (
        'id',

        'date',
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

        'user',
        'daily_health_status',
        'daily_intakes_report',

        'created_at',
        'updated_at',
    )
    raw_id_fields = ('daily_health_status', 'daily_intakes_report')
    date_hierarchy = 'started_at'
    search_fields = (
        'daily_health_status__user__pk',
        'daily_health_status__user__email',
        'daily_health_status__user__username',
    )
    list_filter = (
        'is_completed',
        ('finished_at', EmptyFieldListFilter),
        'dialysate_color',
        ('notes', EmptyFieldListFilter),
    )

    def get_queryset(self, request):
        # noinspection PyUnresolvedReferences
        return super().get_queryset(request).prefetch_all_related()

    def user(self, obj):
        return obj.daily_health_status.user

    def weight_kg(self, obj):
        return obj.daily_health_status.weight_kg

    weight_kg.admin_order_field = "daily_health_status__weight_kg"

    def urine_ml(self, obj):
        return obj.daily_health_status.urine_ml

    urine_ml.admin_order_field = "daily_health_status__urine_ml"

    def date(self, obj):
        return obj.daily_health_status.date

    urine_ml.admin_order_field = "daily_health_status__date"
