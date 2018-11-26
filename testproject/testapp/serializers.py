from django.contrib.auth import get_user_model

from djoser.serializers import UserSerializer
from rest_framework import serializers


class ExtendedUserSerializer(UserSerializer):
    phone_number = serializers.CharField(allow_blank=True)

    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'username', 'phone_number', 'yubikey_id')
