from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from testapp.models import User


class ExtendedUserSerializer(ModelSerializer):
    phone_number = serializers.CharField(allow_blank=True)

    class Meta:
        model = get_user_model()
        fields = ("id", "email", "username", "phone_number")
        read_only_fields = (User.USERNAME_FIELD,)
