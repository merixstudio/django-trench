from rest_framework import serializers
from djoser.serializers import UserSerializer
from django.contrib.auth import get_user_model

class ExtendedUserSerializer(UserSerializer):
    phone_number = serializers.CharField(allow_blank=True)

    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'username', 'phone_number')
