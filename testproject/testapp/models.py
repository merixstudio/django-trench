from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import AutoField


class User(AbstractUser):
    id = AutoField(primary_key=True)
    phone_number = models.CharField(max_length=12, blank=True)
