from django.core.exceptions import ValidationError
from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

import resend

from apps.users.models import User, PasswordResetCode
from apps.users.serializers.user_serializer import UserSerializer


class UserViewSet(viewsets.GenericViewSet):
    """
    ViewSet para gestionar operaciones relacionadas con usuarios
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ['create', 'request_code', 'reset_password']:
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
    operation_description="Solicita un código de verificación para restablecer la contraseña",
    request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['email']
        ),
        responses={
            200: "Código enviado exitosamente",
            400: "Datos inválidos",
            404: "Usuario no encontrado"
        }
    )
    @action(detail=False, methods=['post'])
    def request_code(self, request):
        """
        Envía un código de verificación al email proporcionado.

        Request:
        {
            "email": "string - Correo electrónico del usuario"
        }

        Response:
        {
            "message": "string - Mensaje de confirmación"
        }
        """
        try:
            email = request.data.get('email')
            
            if not email:
                return Response(
                    {'error': 'El email es requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verificar que el usuario existe
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {'error': 'No existe un usuario con este email'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Si hay un código válido existente, lo invalidamos
            PasswordResetCode.objects.filter(
                email=email, 
                is_used=False
            ).update(is_used=True)

            # Crear nuevo código
            reset_code = PasswordResetCode.objects.create(email=email)
            
            # Enviar email usando el backend de email de Django
            send_mail(
                'Código de recuperación',  # asunto
                f'Tu código de verificación es: {reset_code.code}',  # mensaje
                settings.EMAIL_HOST_USER,  # remitente
                [email],  # destinatario
                fail_silently=False,  # si es False, levantará excepciones en caso de error
            )

            return Response({
                'message': 'Si el correo existe en nuestra base de datos, recibirás un código de verificación'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="Restablece la contraseña usando el código de verificación",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'code': openapi.Schema(type=openapi.TYPE_STRING),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING),
                'confirm_password': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['email', 'code', 'new_password', 'confirm_password']
        ),
        responses={
            200: "Contraseña actualizada exitosamente",
            400: "Datos inválidos o código expirado",
            404: "Usuario no encontrado"
        }
    )
    @action(detail=False, methods=['post'])
    def reset_password(self, request):
        """
        Restablece la contraseña usando un código de verificación.

        Request:
        {
            "email": "string - Correo electrónico del usuario",
            "code": "string - Código de verificación",
            "new_password": "string - Nueva contraseña",
            "confirm_password": "string - Confirmación de la nueva contraseña"
        }

        Response:
        {
            "message": "string - Mensaje de confirmación"
        }
        """
        try:
            email = request.data.get('email')
            code = request.data.get('code')
            new_password = request.data.get('new_password')
            confirm_password = request.data.get('confirm_password')

            if not all([email, code, new_password, confirm_password]):
                return Response(
                    {'error': 'Todos los campos son requeridos'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if new_password != confirm_password:
                return Response(
                    {'error': 'Las contraseñas no coinciden'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            reset_code = PasswordResetCode.objects.filter(
                email=email,
                code=code,
                is_used=False
            ).order_by('-created_at').first()

            if not reset_code or not reset_code.is_valid:
                return Response(
                    {'error': 'Código inválido o expirado'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()

            reset_code.is_used = True
            reset_code.save()

            return Response({
                'message': 'Contraseña actualizada correctamente'
            })

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
