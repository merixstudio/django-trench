from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from trench import serializers
from trench.command.activate_mfa_method import activate_mfa_method_command
from trench.command.create_mfa_method import create_mfa_method_command
from trench.command.deactivate_mfa_method import deactivate_mfa_method
from trench.exceptions import MFAMethodDoesNotExistError, MFAValidationError
from trench.serializers import (
    MFAMethodActivationConfirmationValidator,
    MFAMethodDeactivationValidator,
    generate_model_serializer,
)
from trench.settings import api_settings
from trench.utils import (
    generate_backup_codes,
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
        except MFAValidationError as cause:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, data={"error": str(cause)}
            )

        return Response({"backup_codes": backup_codes})


class RequestMFAMethodDeactivationView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request, method: str) -> Response:
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


class RequestMFAMethodBackupCodesRegenerationView(GenericAPIView):
    serializer_class = (
        serializers.RequestMFAMethodBackupCodesRegenerationSerializer
    )  # noqa
    permission_classes = (IsAuthenticated,)
    http_method_names = ["post"]

    def get_serializer_context(self):
        context = super().get_serializer_context()

        try:
            context.update(
                {
                    "name": self.kwargs["method"],
                    "obj": self.obj,
                    "conf": api_settings.MFA_METHODS[self.kwargs["method"]],
                }
            )
        except KeyError:
            raise NotFound()

        return context

    def post(self, request, *args, **kwargs):
        self.mfa_method_name = kwargs.get("method")
        self.obj = get_object_or_404(
            MFAMethod, user=request.user, name=self.mfa_method_name
        )

        if not self.obj.is_active:
            return Response(
                {"error": _("Method is disabled.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        backup_codes = generate_backup_codes()

        if requires_encryption:
            self.obj.backup_codes = [
                make_password(backup_code) for backup_code in backup_codes
            ]
        else:  # pragma: no cover
            self.obj.backup_codes = backup_codes

        self.obj.save(update_fields=["_backup_codes"])
        return Response({"backup_codes": backup_codes})


class GetMFAConfig(APIView):
    def get(self, request, *args, **kwargs):
        available_methods = [
            (k, v.get("VERBOSE_NAME")) for k, v in api_settings.MFA_METHODS.items()
        ]

        return Response(
            {
                "methods": available_methods,
                "confirm_disable_with_code": api_settings.CONFIRM_DISABLE_WITH_CODE,  # noqa
                "confirm_regeneration_with_code": api_settings.CONFIRM_BACKUP_CODES_REGENERATION_WITH_CODE,  # noqa
                "allow_backup_codes_regeneration": api_settings.ALLOW_BACKUP_CODES_REGENERATION,  # noqa
            },
            status=status.HTTP_200_OK,
        )


class ListUserActiveMFAMethods(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        active_mfa_methods = MFAMethod.objects.filter(user=request.user, is_active=True)
        serializer = serializers.UserMFAMethodSerializer(active_mfa_methods, many=True)
        return Response(serializer.data)


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
