from django.urls import path
from drf_spectacular.views import SpectacularJSONAPIView, SpectacularSwaggerView

from api import views

urlpatterns = [
    path('user/profile/', views.UserProfileView.as_view(), name="api-user-profile"),
    path('user/app-review/', views.UserAppReview.as_view(), name="api-user-app-review"),
    path('user/', views.UserView.as_view(), name="api-user"),

    path('general-recommendations/', views.GeneralRecommendationsView.as_view(), name="api-general-recommendations"),

    path('nutrition/products/', views.ProductListView.as_view(), name="api-products"),
    path('nutrition/products/search/', views.ProductSearchView.as_view(), name="api-products-search"),

    path('nutrition/daily-reports/light/', views.DailyIntakesReportsLightView.as_view(),
         name="api-daily-reports"),

    path('nutrition/daily-reports/<str:date>/', views.DailyIntakesReportView.as_view(),
         name="api-daily-report"),

    path('nutrition/intake/', views.IntakeCreateView.as_view(), name="api-intake"),
    path('nutrition/intake/<int:id>/', views.IntakeView.as_view(), name="api-intake"),
    path('nutrition/screen/', views.NutritionScreenView.as_view(), name="api-nutrition-screen"),
    path('nutrition/screen/v2/', views.NutritionScreenV2View.as_view(), name="api-nutrition-screen-v2"),
    path('nutrition/weekly/', views.NutritionWeeklyScreenView.as_view(), name="api-nutrition-weekly-screen"),

    path('health-status/blood-pressure/', views.BloodPressureCreateView.as_view(), name="api-blood-pressure-create"),
    path('health-status/blood-pressure/<int:id>/', views.BloodPressureUpdateView.as_view(),
         name="api-blood-pressure-update"),

    path('health-status/pulse/', views.PulseCreateView.as_view(), name="api-pulse-create"),
    path('health-status/pulse/<int:id>/', views.PulseUpdateView.as_view(), name="api-pulse-update"),

    path('health-status/screen/', views.HealthStatusScreenView.as_view(), name="api-health-status-screen"),
    path('health-status/weekly/', views.HealthStatusWeeklyScreenView.as_view(), name="api-health-status-weekly"),
    path('health-status/<str:date>/', views.DailyHealthStatusByDateView.as_view(), name="api-health-status-by-date"),
    path('health-status/', views.DailyHealthStatusView.as_view(), name="api-health-status"),


    path('peritoneal-dialysis/manual/dialysis/create/', views.CreateManualPeritonealDialysisLegacyView.as_view(),
         name="api-peritoneal-dialysis-manual-create"),

    path('peritoneal-dialysis/manual/dialysis/<int:id>/', views.UpdateManualPeritonealDialysisView.as_view(),
         name="api-peritoneal-dialysis-manual-dialysis"),

    path('peritoneal-dialysis/manual/screen/v2/', views.ManualPeritonealDialysisScreenView.as_view(),
         name="api-peritoneal-dialysis-manual-screen"),

    # All others are deprecated
    path('peritoneal-dialysis/manual/', views.CreateManualPeritonealDialysisLegacyView.as_view(),
         name="api-peritoneal-dialysis-manual-create-deprecated"),

    path('peritoneal-dialysis/manual/screen/', views.ManualPeritonealDialysisLegacyScreenView.as_view(),
         name="api-peritoneal-dialysis-manual-screen-deprecated"),

    path('peritoneal-dialysis/manual/reports/', views.ManualPeritonealDialysisReportsView.as_view(),
         name="api-peritoneal-dialysis-manual-reports-deprecated"),

    path('peritoneal-dialysis/manual/reports/paginated/', views.ManualPeritonealDialysisReportsPaginatedView.as_view(),
         name="api-peritoneal-dialysis-manual-reports-paginated"),

    path('peritoneal-dialysis/manual/<int:id>/', views.UpdateManualPeritonealDialysisLegacyView.as_view(),
         name="api-peritoneal-dialysis-manual-update-deprecated"),


    path('schema.json/', SpectacularJSONAPIView.as_view(), name='schema'),
    # Optional UI:
    path('', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
