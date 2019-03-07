from django.contrib.auth.hashers import make_password
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from trench import serializers
from trench.settings import api_settings
from trench.utils import (
    generate_backup_codes,
    get_mfa_model,
    user_token_generator,
)


MFAMethod = get_mfa_model()
requires_encryption = api_settings.ENCRYPT_BACKUP_CODES


class MFACredentialsLoginMixin:
    """
    Mixin handling user log in. Checks if primary MFA method
    is active and dispatches code if so. Else calls handle_user_login.
    """
    serializer_class = serializers.LoginSerializer
    permission_classes = (AllowAny, )

    def handle_mfa_response(self, user, mfa_method, *args, **kwargs):
        data = {
            'ephemeral_token': user_token_generator.make_token(user),
            'method': mfa_method.name,
            'other_methods': serializers.UserMFAMethodSerializer(
                user.mfa_methods.filter(is_active=True, is_primary=False),
                many=True,
            ).data,
        }
        return Response(data)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        auth_method = (
            user.mfa_methods
                .filter(is_primary=True, is_active=True)
                .first()
        )
        if auth_method:
            conf = api_settings.MFA_METHODS[auth_method.name]
            handler = conf['HANDLER'](
                user=user,
                obj=auth_method,
                conf=conf,
            )
            handler.dispatch_message()
            return self.handle_mfa_response(user, auth_method)

        return self.handle_user_login(
            request=request,
            serializer=serializer,
            *args,
            **kwargs
        )


class MFACodeLoginMixin:
    """
    Mixin handling user login if MFA auth is enabled.
    Expects ephemeral token and valid MFA code.
    Checks against all active MFA methods.
    """
    serializer_class = serializers.CodeLoginSerializer
    permission_classes = (AllowAny, )

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return self.handle_user_login(
            request=request,
            serializer=serializer,
            *args,
            **kwargs
        )


class RequestMFAMethodActivationView(GenericAPIView):
    """
    View handling new MFA method activation requests.
    If validation passes, new MFAMethod (inactive) object
    is created.
    """
    serializer_class = serializers.RequestMFAMethodActivationSerializer
    permission_classes = (IsAuthenticated, )
    http_method_names = ['post']

    def get_serializer_context(self):
        context = super().get_serializer_context()

        try:
            context['name'] = self.kwargs['method']
        except KeyError:
            raise NotFound()

        return context

    def post(self, request, *args, **kwargs):
        self.mfa_method_name = kwargs.get('method')

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj, created = serializer.save()
        if not created and obj.is_active:
            return Response(
                {'error': 'MFA method already active.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conf = api_settings.MFA_METHODS[self.mfa_method_name]

        handler = conf['HANDLER'](
            user=request.user,
            obj=obj,
            conf=conf,
        )
        return Response(handler.dispatch_message(), status=status.HTTP_200_OK)


class RequestMFAMethodActivationConfirmView(GenericAPIView):
    serializer_class = serializers.RequestMFAMethodActivationConfirmSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ['post']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        obj = getattr(self, 'obj', None)

        try:
            context.update({
                'name': self.kwargs['method'],
                'obj': obj,
                'conf': api_settings.MFA_METHODS[self.kwargs['method']],
            })
        except KeyError:
            raise NotFound()

        return context

    def post(self, request, *args, **kwargs):
        self.mfa_method_name = self.kwargs['method']
        self.obj = get_object_or_404(
            MFAMethod, user=request.user, name=self.mfa_method_name)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        backup_codes = generate_backup_codes()

        if requires_encryption:
            self.obj.backup_codes = [
                make_password(backup_code) for backup_code in backup_codes
            ]
        else:  # pragma: no cover
            self.obj.backup_codes = backup_codes

        self.obj.is_active = True
        self.obj.is_primary = not MFAMethod.objects.filter(
            user=request.user,
            is_active=True,
        ).exists()
        self.obj.save(
            update_fields=['is_active', '_backup_codes', 'is_primary']
        )

        return Response({'backup_codes': backup_codes})


class RequestMFAMethodDeactivationView(GenericAPIView):
    serializer_class = serializers.RequestMFAMethodDeactivationSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ['post']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        obj = getattr(self, 'obj', None)

        try:
            context.update({
                'name': self.kwargs['method'],
                'obj': obj,
                'conf': api_settings.MFA_METHODS[self.kwargs['method']],
            })
        except KeyError:
            raise NotFound()

        return context

    def post(self, request, *args, **kwargs):
        self.mfa_method_name = kwargs.get('method')
        self.obj = get_object_or_404(
            MFAMethod, user=request.user, name=self.mfa_method_name)

        if not self.obj.is_active:
            return Response(
                {'error': _('Method already disabled.')},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                default_update_fields = ['is_active']

                if serializer.users_active_methods_count >= 2:
                    new_primary_obj = (
                        getattr(serializer, 'new_method')
                        or MFAMethod.objects  # noqa
                        .filter(user=request.user, is_active=True)
                        .exclude(id=self.obj.id)
                        .first()
                    )

                    new_primary_obj.is_primary = True
                    new_primary_obj.save(update_fields=['is_primary'])

                default_update_fields.append('is_primary')
                self.obj.is_primary = False
                self.obj.is_active = False
                self.obj.save(update_fields=default_update_fields)
        except IntegrityError:  # pragma: no cover
            return Response(  # pragma: no cover
                {
                    'error': _('Failed to update MFA information')
                },  # pragma: no cover
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class RequestMFAMethodBackupCodesRegenerationView(GenericAPIView):
    serializer_class = serializers.RequestMFAMethodBackupCodesRegenerationSerializer  # noqa
    permission_classes = (IsAuthenticated,)
    http_method_names = ['post']

    def get_serializer_context(self):
        context = super().get_serializer_context()

        try:
            context.update({
                'name': self.kwargs['method'],
                'obj': self.obj,
                'conf': api_settings.MFA_METHODS[self.kwargs['method']],
            })
        except KeyError:
            raise NotFound()

        return context

    def post(self, request, *args, **kwargs):
        self.mfa_method_name = kwargs.get('method')
        self.obj = get_object_or_404(
            MFAMethod, user=request.user, name=self.mfa_method_name)

        if not self.obj.is_active:
            return Response(
                {'error': _('Method is disabled.')},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data,)
        serializer.is_valid(raise_exception=True)

        backup_codes = generate_backup_codes()

        if requires_encryption:
            self.obj.backup_codes = [
                make_password(backup_code) for backup_code in backup_codes
            ]
        else:  # pragma: no cover
            self.obj.backup_codes = backup_codes

        self.obj.save(update_fields=['_backup_codes'])
        return Response({'backup_codes': backup_codes})


class GetMFAConfig(APIView):
    def get(self, request, *args, **kwargs):
        available_methods = [(k, v.get('VERBOSE_NAME'))
                             for k, v in api_settings.MFA_METHODS.items()]

        return Response(
            {
                'methods': available_methods,
                'confirm_disable_with_code': api_settings.CONFIRM_DISABLE_WITH_CODE,  # noqa
                'confirm_regeneration_with_code': api_settings.CONFIRM_BACKUP_CODES_REGENERATION_WITH_CODE,  # noqa
                'allow_backup_codes_regeneration': api_settings.ALLOW_BACKUP_CODES_REGENERATION,  # noqa
            },
            status=status.HTTP_200_OK,
        )


class ListUserActiveMFAMethods(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        active_mfa_methods = MFAMethod.objects.filter(
            user=request.user, is_active=True)
        serializer = serializers.UserMFAMethodSerializer(
            active_mfa_methods, many=True)
        return Response(serializer.data)


class RequestMFAMethodCode(GenericAPIView):
    serializer_class = serializers.RequestMFAMethodCodeSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mfa_method_name = serializer.validated_data.get('method')
        if mfa_method_name:
            obj = get_object_or_404(
                MFAMethod,
                user=request.user,
                name=mfa_method_name,
                is_active=True,
            )

        conf = api_settings.MFA_METHODS.get(mfa_method_name)

        if not conf:
            return Response(  # pragma: no cover
                {'error', _('Requested MFA method does not exists')},
                status=status.HTTP_400_BAD_REQUEST,
            )

        handler = conf.get('HANDLER')(
            user=request.user,
            obj=obj,
            conf=conf,
        )
        dispatcher_resp = handler.dispatch_message()
        return Response(dispatcher_resp)


class ChangePrimaryMethod(CreateAPIView):
    serializer_class = serializers.ChangePrimaryMethodSerializer

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)

        return Response(
            serializers.UserMFAMethodSerializer(
                request.user.mfa_methods.filter(is_active=True),
                many=True,
            ).data,
            status=status.HTTP_200_OK,
        )
