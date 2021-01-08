from django_filters import rest_framework as filters

from core.models import Product


class ProductFilter(filters.FilterSet):
    query = filters.CharFilter(field_name="name_lt", lookup_expr='icontains')

    class Meta:
        model = Product
        fields = ('query',)
