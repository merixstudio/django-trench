from django.contrib.auth import (
    get_user_model,
    user_logged_in,
    user_logged_out,
)
from django.db.models import QuerySet

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from trench import serializers
from trench.command.activate_mfa_method import activate_mfa_method_command
from trench.command.authenticate_user import authenticate_user_command
from trench.command.create_mfa_method import create_mfa_method_command
from trench.command.deactivate_mfa_method import deactivate_mfa_method
from trench.command.replace_mfa_method_backup_codes import (
    regenerate_backup_codes_for_mfa_method_command,
)
from trench.command.set_primary_mfa_method import set_primary_mfa_method_command
from trench.exceptions import (
    InvalidTokenError,
    MFAMethodDoesNotExistError,
    MFAValidationError,
)
from trench.query.get_mfa_method import get_mfa_method_query
from trench.query.get_primary_active_mfa_method import (
    get_primary_active_mfa_method_query,
)
from trench.query.get_primary_active_mfa_method_name import (
    get_primary_active_mfa_method_name_query,
)
from trench.query.list_active_mfa_methods import list_active_mfa_methods_query
from trench.serializers import (
    ChangePrimaryMethodValidator,
    LoginSerializer,
    MFALoginValidator,
    MFAMethodActivationConfirmationValidator,
    MFAMethodBackupCodesGenerationValidator,
    MFAMethodDeactivationValidator,
    RequestMFAMethodCodeSerializer,
    TokenSerializer,
    generate_model_serializer,
)
from trench.settings import api_settings
from trench.utils import (
    get_mfa_handler,
    get_mfa_model,
    get_source_field_by_method_name,
    user_token_generator,
    validate_backup_code,
    validate_code,
)


MFAMethod = get_mfa_model()
requires_encryption = api_settings.ENCRYPT_BACKUP_CODES
User = get_user_model()


class MFACredentialsLoginMixin(APIView):
    """
    Mixin handling user log in. Checks if primary MFA method
    is active and dispatches code if so. Else calls handle_user_login.
    """

    permission_classes = (AllowAny,)

    @staticmethod
    def post(request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = authenticate_user_command(
                request=request,
                username=serializer.validated_data[User.USERNAME_FIELD],
                password=serializer.validated_data["password"],
            )
        except MFAValidationError as cause:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, data={"error": str(cause)}
            )
        try:
            mfa_method = get_primary_active_mfa_method_query(user_id=user.id)
            handler = get_mfa_handler(mfa_method=mfa_method)
            handler.dispatch_message()
            return Response(
                data={
                    "ephemeral_token": user_token_generator.make_token(user),
                    "method": mfa_method.name,
                }
            )
        except MFAMethodDoesNotExistError:
            token = RefreshToken.for_user(user=user)
            return Response(
                data={"refresh": str(token), "access": str(token.access_token)}
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


class MFALoginView(APIView):
    @classmethod
    def post(cls, request: Request) -> Response:
        serializer = MFALoginValidator(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = user_token_generator.check_token(
            user=None, token=serializer.validated_data["ephemeral_token"]
        )
        if user is None:
            raise InvalidTokenError()

        is_authenticated = cls._perform_authentication(
            user_id=user.id, code=serializer.validated_data["code"]
        )
        if not is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        token, _ = Token.objects.get_or_create(user=user)
        user_logged_in.send(sender=user.__class__, request=request, user=user)
        return Response(status=status.HTTP_200_OK, data=TokenSerializer(token).data)

    @classmethod
    def _perform_authentication(cls, user_id: int, code: str) -> bool:
        for auth_method in list_active_mfa_methods_query(user_id=user_id):
            validated_backup_code = validate_backup_code(
                value=code, backup_codes=auth_method.backup_codes
            )
            if validate_code(code=code, mfa_method=auth_method):
                return True
            if validated_backup_code:
                auth_method.remove_backup_code(validated_backup_code)
                return True
        return False


class MFALogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request: Request) -> Response:
        Token.objects.filter(user=request.user).delete()
        user_logged_out.send(
            sender=request.user.__class__, request=request, user=request.user
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


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
        handler = get_mfa_handler(mfa_method=mfa)
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


class RequestMFAMethodCode(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request: Request) -> Response:
        serializer = RequestMFAMethodCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            method = serializer.validated_data.get("method")
            if method is None:
                method = get_primary_active_mfa_method_name_query(
                    user_id=request.user.id
                )
            mfa = get_mfa_method_query(user_id=request.user.id, name=method)
            handler = get_mfa_handler(mfa_method=mfa)
            return Response(handler.dispatch_message())
        except MFAValidationError as cause:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, data={"error": str(cause)}
            )


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
