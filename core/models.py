from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models, transaction


class CustomUserManager(UserManager):
    def get(self, *args, **kwargs):
        return super().select_related("profile").get(*args, **kwargs)


class User(AbstractUser):
    objects = CustomUserManager()

    email = models.EmailField(unique=True)

    @transaction.atomic()
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)

    @transaction.atomic()
    def delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)
