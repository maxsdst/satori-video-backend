from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class CustomUserManager(UserManager):
    def get(self, *args, **kwargs):
        return super().select_related("profile").get(*args, **kwargs)


class User(AbstractUser):
    objects = CustomUserManager()

    email = models.EmailField(unique=True)
