from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from trench import serializers
from trench.command.activate_mfa_method import activate_mfa_method_command
from trench.command.create_mfa_method import create_mfa_method_command
from trench.command.deactivate_mfa_method import deactivate_mfa_method
from trench.command.replace_mfa_method_backup_codes import (
    regenerate_backup_codes_for_mfa_method_command,
)
from trench.command.set_primary_mfa_method import set_primary_mfa_method_command
from trench.exceptions import MFAMethodDoesNotExistError, MFAValidationError
from trench.query.get_primary_active_mfa_method_name import (
    get_primary_active_mfa_method_name_query,
)
from trench.query.list_active_mfa_methods import list_active_mfa_methods_query
from trench.serializers import (
    ChangePrimaryMethodValidator,
    MFAMethodActivationConfirmationValidator,
    MFAMethodBackupCodesGenerationValidator,
    MFAMethodDeactivationValidator,
    generate_model_serializer,
)
from trench.settings import api_settings
from trench.utils import (
    get_method_config_by_name,
    get_mfa_model,
    get_source_field_by_method_name,
    user_token_generator,
)


MFAMethod = get_mfa_model()
requires_encryption = api_settings.ENCRYPT_BACKUP_CODES
User = get_user_model()


class MFACredentialsLoginMixin(GenericAPIView):
    """
    Mixin handling user log in. Checks if primary MFA method
    is active and dispatches code if so. Else calls handle_user_login.
    """

    serializer_class = serializers.LoginSerializer
    permission_classes = (AllowAny,)

    def handle_mfa_response(self, user: User, mfa_method: MFAMethod, *args, **kwargs):
        data = {
            "ephemeral_token": user_token_generator.make_token(user),
            "method": mfa_method.name,
            "other_methods": serializers.UserMFAMethodSerializer(
                user.mfa_methods.filter(is_active=True, is_primary=False),
                many=True,
            ).data,
        }
        return Response(data)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        auth_method = user.mfa_methods.filter(is_primary=True, is_active=True).first()
        if auth_method:
            conf = api_settings.MFA_METHODS[auth_method.name]
            handler = conf["HANDLER"](
                user=user,
                obj=auth_method,
                conf=conf,
            )
            handler.dispatch_message()
            return self.handle_mfa_response(user, auth_method)

        return self.handle_user_login(
            request=request, serializer=serializer, *args, **kwargs
        )


class MFACodeLoginMixin(GenericAPIView):
    """
    Mixin handling user login if MFA auth is enabled.
    Expects ephemeral token and valid MFA code.
    Checks against all active MFA methods.
    """

    serializer_class = serializers.CodeLoginSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return self.handle_user_login(
            request=request, serializer=serializer, *args, **kwargs
        )


class RequestMFAMethodActivationView(APIView):
    """
    View handling new MFA method activation requests.
    If validation passes, new MFAMethod (inactive) object
    is created. The method will be activated after confirmation.
    """

    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request: Request, method: str) -> Response:
        try:
            source_field = get_source_field_by_method_name(name=method)
        except MFAMethodDoesNotExistError as cause:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, data={"errors": str(cause)}
            )
        if source_field is not None:
            serializer_class = generate_model_serializer(
                name="MFAMethodActivationValidator",
                model=request.user.__class__,
                fields=(source_field,),
            )
            serializer = serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
        try:
            mfa = create_mfa_method_command(
                user_id=request.user.id,
                name=method,
            )
        except MFAValidationError as cause:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"error": str(cause)},
            )
        conf = get_method_config_by_name(name=method)
        handler = conf["HANDLER"](
            user=request.user,
            obj=mfa,
            conf=conf,
        )
        return Response(handler.dispatch_message(), status=status.HTTP_200_OK)


class RequestMFAMethodActivationConfirmView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request: Request, method: str) -> Response:
        serializer = MFAMethodActivationConfirmationValidator(
            mfa_method_name=method, user=request.user, data=request.data
        )
        if not serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer.errors)
        try:
            backup_codes = activate_mfa_method_command(
                user_id=request.user.id,
                name=method,
                code=serializer.validated_data["code"],
            )
            return Response({"backup_codes": backup_codes})
        except MFAValidationError as cause:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, data={"error": str(cause)}
            )


class RequestMFAMethodDeactivationView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request: Request, method: str) -> Response:
        serializer = MFAMethodDeactivationValidator(
            mfa_method_name=method, user=request.user, data=request.data
        )
        if not serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer.errors)
        try:
            deactivate_mfa_method(mfa_method_name=method, user_id=request.user.id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except MFAValidationError as cause:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, data={"error": str(cause)}
            )


class RequestMFAMethodBackupCodesRegenerationView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request: Request, method: str) -> Response:
        serializer = MFAMethodBackupCodesGenerationValidator(
            mfa_method_name=method, user=request.user, data=request.data
        )
        if not serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer.errors)
        try:
            backup_codes = regenerate_backup_codes_for_mfa_method_command(
                user_id=request.user.id,
                name=method,
            )
            return Response({"backup_codes": backup_codes})
        except MFAValidationError as cause:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, data={"error": str(cause)}
            )


class GetMFAConfig(APIView):
    @staticmethod
    def get(request: Request) -> Response:
        available_methods = [
            (k, v.get("VERBOSE_NAME")) for k, v in api_settings.MFA_METHODS.items()
        ]
        return Response(
            data={
                "methods": available_methods,
                "confirm_disable_with_code": api_settings.CONFIRM_DISABLE_WITH_CODE,  # noqa
                "confirm_regeneration_with_code": api_settings.CONFIRM_BACKUP_CODES_REGENERATION_WITH_CODE,  # noqa
                "allow_backup_codes_regeneration": api_settings.ALLOW_BACKUP_CODES_REGENERATION,  # noqa
            },
        )


class ListUserActiveMFAMethods(ListAPIView):
    serializer_class = serializers.UserMFAMethodSerializer

    def get_queryset(self) -> QuerySet:
        return list_active_mfa_methods_query(user_id=self.request.user.id)


class RequestMFAMethodCode(GenericAPIView):
    serializer_class = serializers.RequestMFAMethodCodeSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mfa_method_name = serializer.validated_data.get("method")
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
                {"error", _("Requested MFA method does not exists")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        handler = conf.get("HANDLER")(
            user=request.user,
            obj=obj,
            conf=conf,
        )
        dispatcher_resp = handler.dispatch_message()
        return Response(dispatcher_resp)


class ChangePrimaryMethod(APIView):
    @staticmethod
    def post(request: Request) -> Response:
        mfa_method_name = get_primary_active_mfa_method_name_query(
            user_id=request.user.id
        )
        print(mfa_method_name)
        serializer = ChangePrimaryMethodValidator(
            user=request.user, mfa_method_name=mfa_method_name, data=request.data
        )
        serializer.is_valid(raise_exception=True)
        try:
            set_primary_mfa_method_command(
                user_id=request.user.id, name=serializer.validated_data["method"]
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except MFAValidationError as cause:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, data={"error": str(cause)}
            )
