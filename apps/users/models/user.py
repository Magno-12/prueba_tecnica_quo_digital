from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.default.models.base_model import BaseModel
from apps.users.managers.user_manager import UserManager


class User(AbstractUser, BaseModel):
    objects = UserManager()
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email  # Usar email como username
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
