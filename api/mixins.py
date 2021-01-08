from typing import Dict

from rest_framework.generics import GenericAPIView


class OverrideSerializerDataMixin(GenericAPIView):
    def override_data(self, data: Dict) -> Dict:
        if self.lookup_field:
            data[self.lookup_field] = self.kwargs[self.lookup_url_kwarg or self.lookup_field]

        return data

    def get_serializer(self, *args, **kwargs):
        if 'data' in kwargs:
            data = kwargs.pop('data')
            data = self.override_data(data)

            return super().get_serializer(*args, data=data, **kwargs)
        else:
            return super().get_serializer(*args, **kwargs)
