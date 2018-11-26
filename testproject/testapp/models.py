from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator
from django.db import models


class User(AbstractUser):
    phone_number = models.CharField(max_length=12, blank=True)

    yubikey_id = models.CharField(
        validators=[
            MinLengthValidator(12)
        ],
        max_length=12,
        blank=True,
    )
