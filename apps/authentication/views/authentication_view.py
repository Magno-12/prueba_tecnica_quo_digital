from django.contrib.auth.hashers import check_password

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.users.models import User
from apps.authentication.serializers.authentication_serializer import (
    AuthenticationSerializer,
    LogoutSerializer,
)


class AuthenticationViewSet(GenericViewSet):
    """
    ViewSet para manejar la autenticación de usuarios.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'login':
            return AuthenticationSerializer
        return LogoutSerializer

    @swagger_auto_schema(
        operation_description="Inicia sesión de usuario con email y contraseña",
        request_body=AuthenticationSerializer,
        responses={
            200: openapi.Response(
                description="Login exitoso",
                examples={
                    "application/json": {
                        "tokens": {
                            "refresh": "string",
                            "access": "string"
                        },
                        "user": {
                            "id": "uuid",
                            "email": "testmagno@test.com",
                            "first_name": "Magno",
                            "last_name": "Test"
                        }
                    }
                }
            ),
            401: "Credenciales inválidas"
        }
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        Inicia sesión de usuario y devuelve tokens JWT.

        Request:
        {
            "email": "user@example.com",
            "password": "string"
        }

        Response:
        {
            "tokens": {
                "refresh": "string - Token de refresco JWT",
                "access": "string - Token de acceso JWT"
            },
            "user": {
                "id": "integer - ID del usuario",
                "email": "string - Correo electrónico",
                "first_name": "string - Nombre",
                "last_name": "string - Apellido"
            }
        }

        Errores:
        - 401: Usuario no existe / Contraseña incorrecta / Cuenta desactivada
        - 400: Datos de entrada inválidos
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_data = serializer.validated_data

        try:
            user = User.objects.get(email=user_data['email'])
        except User.DoesNotExist:
            raise AuthenticationFailed(
                "El usuario con este email no existe"
            )

        if not check_password(user_data['password'], user.password):
            raise AuthenticationFailed("Contraseña incorrecta")

        if not user.is_active:
            raise AuthenticationFailed("Esta cuenta ha sido desactivada")

        refresh = RefreshToken.for_user(user)

        return Response({
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Cierra la sesión del usuario",
        request_body=LogoutSerializer,
        responses={
            200: openapi.Response(
                description="Sesión cerrada exitosamente",
                examples={
                    "application/json": {
                        "message": "Sesión cerrada exitosamente"
                    }
                }
            ),
            400: openapi.Response(
                description="Token inválido",
                examples={
                    "application/json": {
                        "error": "Token inválido o expirado"
                    }
                }
            )
        }
    )
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """
        Cierra la sesión del usuario invalidando el token de refresco.

        Request:
        {
            "refresh_token": "string - Token de refresco JWT"
        }

        Response:
        {
            "message": "string - Mensaje de confirmación"
        }

        Errores:
        - 400: Token inválido o expirado
        - 401: No autorizado (token de acceso inválido)
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data['refresh_token']

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {"error": "Token inválido o expirado"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"message": "Sesión cerrada exitosamente"},
            status=status.HTTP_200_OK
        )
