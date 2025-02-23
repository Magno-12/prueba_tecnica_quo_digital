from django.core.exceptions import ValidationError
from django.db import transaction

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.users.models import User
from apps.users.serializers.user_serializer import UserSerializer


class UserViewSet(viewsets.GenericViewSet):
    """
    ViewSet para gestionar operaciones relacionadas con usuarios
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @swagger_auto_schema(
        operation_description="Crea un nuevo usuario en el sistema",
        request_body=UserSerializer,
        responses={
            201: openapi.Response(
                description="Usuario creado exitosamente",
                examples={
                    "application/json": {
                        "user": {
                            "id": 1,
                            "email": "user@example.com",
                            "first_name": "John",
                            "last_name": "Doe"
                        }
                    }
                }
            ),
            400: "Datos inválidos"
        }
    )
    def create(self, request):
        """
        Crea un nuevo usuario en el sistema.

        Request:
        {
            "email": "string - Correo electrónico del usuario",
            "password": "string - Contraseña del usuario",
            "first_name": "string - Nombre del usuario",
            "last_name": "string - Apellido del usuario"
        }

        Response:
        {
            "user": {
                "id": "integer - ID del usuario creado",
                "email": "string - Correo electrónico",
                "first_name": "string - Nombre",
                "last_name": "string - Apellido"
            }
        }

        Errores:
        - 400: Datos de entrada inválidos
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.set_password(request.data['password'])
            user.save()

            return Response({
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Elimina la cuenta del usuario",
        responses={
            204: "Cuenta eliminada exitosamente",
            403: "No autorizado para eliminar esta cuenta",
            404: "Usuario no encontrado"
        }
    )
    @transaction.atomic
    def destroy(self, request, pk=None):
        """
        Elimina la cuenta del usuario. Un usuario solo puede eliminar su propia cuenta.

        Response:
        - 204: No Content (eliminación exitosa)

        Errores:
        - 403: Intento de eliminar cuenta de otro usuario
        - 404: Usuario no encontrado
        """
        try:
            if str(request.user.id) != pk:
                return Response(
                    {"error": "Solo puedes eliminar tu propia cuenta"},
                    status=status.HTTP_403_FORBIDDEN
                )

            user = self.get_queryset().get(pk=pk)
            user.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Restablece la contraseña del usuario",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING),
                'confirm_password': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['email', 'new_password', 'confirm_password']
        ),
        responses={
            200: openapi.Response(
                description="Contraseña actualizada exitosamente",
                examples={
                    "application/json": {
                        "message": "Contraseña actualizada correctamente"
                    }
                }
            ),
            400: "Datos inválidos",
            404: "Usuario no encontrado"
        }
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def reset_password(self, request):
        """
        Restablece la contraseña de un usuario cuando la ha olvidado.

        Request:
        {
            "email": "string - Correo electrónico del usuario",
            "new_password": "string - Nueva contraseña",
            "confirm_password": "string - Confirmación de la nueva contraseña"
        }

        Response:
        {
            "message": "string - Mensaje de confirmación"
        }

        Errores:
        - 400: Datos faltantes o contraseñas no coinciden
        - 404: Usuario no encontrado
        """
        try:
            email = request.data.get('email')
            new_password = request.data.get('new_password')
            confirm_password = request.data.get('confirm_password')

            if not email or not new_password or not confirm_password:
                return Response(
                    {'error': 'Se requieren email y la nueva contraseña'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if new_password != confirm_password:
                return Response(
                    {'error': 'Las contraseñas no coinciden'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()

            return Response({
                'message': 'Contraseña actualizada correctamente',
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {'error': 'No existe un usuario con este email'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
