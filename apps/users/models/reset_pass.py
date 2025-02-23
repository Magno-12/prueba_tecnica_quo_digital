import random
import string
from django.db import models
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.default.models.base_model import BaseModel


class PasswordResetCode(BaseModel):
    """
    Modelo para gestionar los códigos de restablecimiento de contraseña.
    El código expira después de 10 minutos y solo puede usarse una vez.
    """
    email = models.EmailField(
        verbose_name="Email",
        help_text="Email del usuario que solicita el cambio de contraseña"
    )
    code = models.CharField(
        max_length=8,
        verbose_name="Código de verificación",
        help_text="Código alfanumérico de 8 caracteres"
    )
    is_used = models.BooleanField(
        default=False,
        verbose_name="¿Usado?",
        help_text="Indica si el código ya fue utilizado"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    expires_at = models.DateTimeField(
        verbose_name="Fecha de expiración",
        help_text="El código expira después de 10 minutos"
    )

    class Meta:
        verbose_name = "Código de restablecimiento"
        verbose_name_plural = "Códigos de restablecimiento"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.code:
            # Generar código alfanumérico de 8 caracteres
            characters = string.ascii_uppercase + string.digits
            self.code = ''.join(random.choices(characters, k=8))

        if not self.expires_at:
            # El código expira en 10 minutos
            self.expires_at = timezone.now() + timedelta(minutes=10)

        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        """Verifica si el código es válido y no ha expirado"""
        return not self.is_used and self.expires_at > timezone.now()

    def clean(self):
        """Validaciones adicionales del modelo"""
        if self.expires_at <= timezone.now():
            raise ValidationError("La fecha de expiración debe ser futura")

        if self.is_used:
            raise ValidationError("Este código ya ha sido utilizado")

    def __str__(self):
        return f"Código para {self.email} - {'Usado' if self.is_used else 'No usado'}"
