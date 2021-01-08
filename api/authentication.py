from drf_firebase_token_auth.authentication import FirebaseTokenAuthentication as BaseFirebaseAuthentication
from drf_spectacular.extensions import OpenApiAuthenticationExtension


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
    pass
