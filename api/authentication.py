import base64
from typing import Optional

from django.utils import timezone
from drf_firebase_token_auth.authentication import FirebaseTokenAuthentication as BaseFirebaseAuthentication, Tuple
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from django.core.cache import cache

from core.models import User


class FirebaseAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = 'api.authentication.FirebaseAuthentication'
    name = 'firebaseAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'Bearer',
        }


class FirebaseAuthentication(BaseFirebaseAuthentication):

    def cache_key_name(self, token: str) -> str:
        return f'django-rest-framework-user-pk-by-token-{base64.encodestring(token.encode())}'

    def save_user_to_cache(self, user: User, token: str):
        cache.set(self.cache_key_name(token), user.pk, 600)

    def get_user_from_cache(self, token: str) -> Optional[User]:
        user_pk = cache.get(self.cache_key_name(token), None)

        if user_pk:
            user = User.objects.filter(pk=user_pk).first()

            if user:
                user.last_login = timezone.now()
                user.save(update_fields=['last_login'])

                return user

        return None

    def authenticate_credentials(self, token: str) -> Tuple[User, None]:
        user_from_cache = self.get_user_from_cache(token)
        if user_from_cache:
            return user_from_cache, None

        user, _ = super().authenticate_credentials(token)
        self.save_user_to_cache(user, token)

        return user, None
