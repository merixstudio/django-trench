from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from abc import ABC, abstractmethod
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
)
from rest_framework.views import APIView

from trench.backends.provider import get_mfa_handler
from trench.command.activate_mfa_method import activate_mfa_method_command
from trench.command.authenticate_second_factor import authenticate_second_step_command
from trench.command.authenticate_user import authenticate_user_command
from trench.command.create_mfa_method import create_mfa_method_command
from trench.command.deactivate_mfa_method import deactivate_mfa_method_command
from trench.command.replace_mfa_method_backup_codes import (
    regenerate_backup_codes_for_mfa_method_command,
)
from trench.command.set_primary_mfa_method import set_primary_mfa_method_command
from trench.exceptions import MFAMethodDoesNotExistError, MFAValidationError
from trench.query.get_mfa_config_by_name import get_mfa_config_by_name_query
from trench.responses import ErrorResponse
from trench.serializers import (
    ChangePrimaryMethodValidator,
    CodeLoginSerializer,
    LoginSerializer,
    MFAMethodActivationConfirmationValidator,
    MFAMethodBackupCodesGenerationValidator,
    MFAMethodCodeSerializer,
    MFAMethodDeactivationValidator,
    UserMFAMethodSerializer,
    generate_model_serializer,
)
from trench.settings import SOURCE_FIELD, trench_settings
from trench.utils import available_method_choices, get_mfa_model, user_token_generator


class MFAStepMixin(APIView, ABC):
    permission_classes = (AllowAny,)

    @abstractmethod
    def _successful_authentication_response(self, user: User) -> Response:
        raise NotImplementedError


class MFAFirstStepMixin(MFAStepMixin, ABC):
    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = authenticate_user_command(
                request=request,
                username=serializer.validated_data[User.USERNAME_FIELD],
                password=serializer.validated_data["password"],
            )
        except MFAValidationError as cause:
            return ErrorResponse(error=cause)
        try:
            mfa_model = get_mfa_model()
            mfa_method = mfa_model.objects.get_primary_active(user_id=user.id)
            get_mfa_handler(mfa_method=mfa_method).dispatch_message()
            return Response(
                data={
                    "ephemeral_token": user_token_generator.make_token(user),
                    "method": mfa_method.name,
                }
            )
        except MFAMethodDoesNotExistError:
            return self._successful_authentication_response(user=user)


class MFASecondStepMixin(MFAStepMixin, ABC):
    def post(self, request: Request) -> Response:
        serializer = CodeLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = authenticate_second_step_command(
                code=serializer.validated_data["code"],
                ephemeral_token=serializer.validated_data["ephemeral_token"],
            )
            return self._successful_authentication_response(user=user)
        except MFAValidationError as cause:
            return ErrorResponse(error=cause, status=HTTP_401_UNAUTHORIZED)


class MFAMethodActivationView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request: Request, method: str) -> Response:
        try:
            source_field = get_mfa_config_by_name_query(name=method).get(SOURCE_FIELD)
        except MFAMethodDoesNotExistError as cause:
            return ErrorResponse(error=cause)
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
            return ErrorResponse(error=cause)
        return get_mfa_handler(mfa_method=mfa).dispatch_message()


class MFAMethodConfirmActivationView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request: Request, method: str) -> Response:
        serializer = MFAMethodActivationConfirmationValidator(
            mfa_method_name=method, user=request.user, data=request.data
        )
        if not serializer.is_valid():
            return Response(status=HTTP_400_BAD_REQUEST, data=serializer.errors)
        try:
            backup_codes = activate_mfa_method_command(
                user_id=request.user.id,
                name=method,
                code=serializer.validated_data["code"],
            )
            return Response({"backup_codes": backup_codes})
        except MFAValidationError as cause:
            return ErrorResponse(error=cause)


class MFAMethodDeactivationView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request: Request, method: str) -> Response:
        serializer = MFAMethodDeactivationValidator(
            mfa_method_name=method, user=request.user, data=request.data
        )
        if not serializer.is_valid():
            return Response(status=HTTP_400_BAD_REQUEST, data=serializer.errors)
        try:
            deactivate_mfa_method_command(
                mfa_method_name=method, user_id=request.user.id
            )
            return Response(status=HTTP_204_NO_CONTENT)
        except MFAValidationError as cause:
            return ErrorResponse(error=cause)


class MFAMethodBackupCodesRegenerationView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request: Request, method: str) -> Response:
        if not trench_settings.ALLOW_BACKUP_CODES_REGENERATION:
            return ErrorResponse(error=_("Backup codes regeneration is not allowed."))
        serializer = MFAMethodBackupCodesGenerationValidator(
            mfa_method_name=method, user=request.user, data=request.data
        )
        if not serializer.is_valid():
            return Response(status=HTTP_400_BAD_REQUEST, data=serializer.errors)
        try:
            backup_codes = regenerate_backup_codes_for_mfa_method_command(
                user_id=request.user.id,
                name=method,
            )
            return Response({"backup_codes": backup_codes})
        except MFAValidationError as cause:
            return ErrorResponse(error=cause)


class MFAConfigView(APIView):
    permission_classes = (AllowAny,)

    @staticmethod
    def get(request: Request) -> Response:
        return Response(
            data={
                "methods": [
                    method_name
                    for method_name, method_verbose_name in available_method_choices()
                ],
                "confirm_disable_with_code": trench_settings.CONFIRM_DISABLE_WITH_CODE,  # noqa
                "confirm_regeneration_with_code": trench_settings.CONFIRM_BACKUP_CODES_REGENERATION_WITH_CODE,  # noqa
                "allow_backup_codes_regeneration": trench_settings.ALLOW_BACKUP_CODES_REGENERATION,  # noqa
            },
        )


class MFAListActiveUserMethodsView(ListAPIView):
    serializer_class = UserMFAMethodSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self) -> QuerySet:
        mfa_model = get_mfa_model()
        return mfa_model.objects.list_active(user_id=self.request.user.id)


class MFAMethodRequestCodeView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request: Request) -> Response:
        serializer = MFAMethodCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            method = serializer.validated_data.get("method")
            mfa_model = get_mfa_model()
            if method is None:
                method = mfa_model.objects.get_primary_active_name(
                    user_id=request.user.id
                )
            mfa = mfa_model.objects.get_by_name(user_id=request.user.id, name=method)
            return get_mfa_handler(mfa_method=mfa).dispatch_message()
        except MFAValidationError as cause:
            return ErrorResponse(error=cause)


class MFAPrimaryMethodChangeView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request: Request) -> Response:
        mfa_model = get_mfa_model()
        mfa_method_name = mfa_model.objects.get_primary_active_name(
            user_id=request.user.id
        )
        serializer = ChangePrimaryMethodValidator(
            user=request.user, mfa_method_name=mfa_method_name, data=request.data
        )
        serializer.is_valid(raise_exception=True)
        try:
            set_primary_mfa_method_command(
                user_id=request.user.id, name=serializer.validated_data["method"]
            )
            return Response(status=HTTP_204_NO_CONTENT)
        except MFAValidationError as cause:
            return ErrorResponse(error=cause)
