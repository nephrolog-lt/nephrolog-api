from datetime import datetime

from django.urls import path, register_converter
from drf_spectacular.views import SpectacularJSONAPIView, SpectacularSwaggerView

from api import views


class DateConverter:
    regex = r'\d{4}-\d{2}-\d{2}'

    def to_python(self, value):
        return datetime.strptime(value, '%Y-%m-%d')

    def to_url(self, value):
        return value


register_converter(DateConverter, 'date')

urlpatterns = [
    path('user/profile/', views.UserProfileView.as_view(), name="api-user-profile"),

    path('nutrition/products/', views.ProductListView.as_view(), name="api-products"),
    path('nutrition/intake/', views.IntakeCreateView.as_view(), name="api-intake"),
    path('nutrition/intake/<int:id>/', views.IntakeView.as_view(), name="api-intake"),
    path('nutrition/screen/', views.NutritionScreenView.as_view(), name="api-nutrition-screen"),
    path('nutrition/weekly/', views.NutritionWeeklyScreenView.as_view(), name="api-nutrition-weekly-screen"),

    path('health-status/screen/', views.HealthStatusScreenView.as_view(), name="api-health-status-screen"),
    path('health-status/weekly/', views.HealthStatusWeeklyScreenView.as_view(), name="api-health-status-weekly"),
    path('health-status/<str:date>/', views.DailyHealthStatusByDateView.as_view(), name="api-health-status-by-date"),
    path('health-status/', views.DailyHealthStatusView.as_view(), name="api-health-status"),

    path('schema.json/', SpectacularJSONAPIView.as_view(), name='schema'),
    # Optional UI:
    path('', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
