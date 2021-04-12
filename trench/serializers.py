from django.contrib.auth import authenticate, get_user_model
from django.db.models import Model
from django.utils.translation import gettext as _

from abc import abstractmethod
from rest_framework.fields import CharField, ChoiceField
from rest_framework.serializers import ModelSerializer, Serializer
from typing import Any, Dict, Iterable, Type

from trench.exceptions import (
    CodeInvalidOrExpiredError,
    InvalidCodeError,
    InvalidTokenError,
    MFAMethodAlreadyActiveError,
    MFAMethodDoesNotExistError,
    MFANotEnabledError,
    OTPCodeMissingError,
    UnauthenticatedError,
    UserAccountDisabledError,
)
from trench.query.get_mfa_method import get_mfa_method
from trench.settings import api_settings
from trench.utils import (
    get_mfa_handler,
    get_mfa_model,
    user_token_generator,
    validate_backup_code,
    validate_code,
)


User = get_user_model()
MFAMethod = get_mfa_model()

mfa_methods_items = api_settings.MFA_METHODS.items()
MFA_METHODS = [(k, v.get("VERBOSE_NAME", _(k))) for k, v in mfa_methods_items]

ContextType = Dict[str, Any]


def generate_model_serializer(name: str, model: Model, fields: Iterable[str]) -> Type:
    meta_subclass = type(
        "Meta",
        (object,),
        {
            "model": model,
            "fields": fields,
        },
    )
    return type(name, (ModelSerializer,), {"Meta": meta_subclass})


class RequestBodyValidator(Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ProtectedActionValidator(RequestBodyValidator):
    code = CharField(required=True)

    @staticmethod
    def _get_validation_method_name() -> str:
        return "validate_code"

    @staticmethod
    @abstractmethod
    def _validate_mfa_method(mfa: MFAMethod):
        pass

    def __init__(self, mfa_method_name: str, user: User, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = user
        self._mfa_method_name = mfa_method_name

    def validate_code(self, value: str) -> str:
        if not value:
            raise OTPCodeMissingError()

        mfa = get_mfa_method(user_id=self._user.id, name=self._mfa_method_name)
        self._validate_mfa_method(mfa)

        validated_backup_code = validate_backup_code(value, mfa.backup_codes)

        handler = get_mfa_handler(mfa)
        validation_method = getattr(handler, self._get_validation_method_name())
        if validation_method(value):
            return value

        if validated_backup_code:
            mfa.remove_backup_code(validated_backup_code)
            return value

        raise CodeInvalidOrExpiredError()


class MFAMethodDeactivationValidator(ProtectedActionValidator):
    @staticmethod
    def _validate_mfa_method(mfa: MFAMethod):
        if not mfa.is_active:
            raise MFANotEnabledError()


class MFAMethodActivationConfirmationValidator(ProtectedActionValidator):
    @staticmethod
    def _get_validation_method_name() -> str:
        return "validate_confirmation_code"

    @staticmethod
    def _validate_mfa_method(mfa: MFAMethod):
        if mfa.is_active:
            raise MFAMethodAlreadyActiveError()


class MFAMethodBackupCodesGenerationValidator(ProtectedActionValidator):
    @staticmethod
    def _validate_mfa_method(mfa: MFAMethod):
        if not mfa.is_active:
            raise MFANotEnabledError()


class RequestMFAMethodCodeSerializer(RequestBodyValidator):
    method = CharField(max_length=255, required=False)

    @staticmethod
    def validate_method(value: str) -> str:
        if value and value not in api_settings.MFA_METHODS:
            raise MFAMethodDoesNotExistError()
        return value


class LoginSerializer(RequestBodyValidator):
    """
    Validates user's credentials.
    """

    password = CharField(style={"input_type": "password"}, write_only=True)

    def __init__(self, *args, **kwargs):
        super(LoginSerializer, self).__init__(*args, **kwargs)
        self.user = None
        self.fields[User.USERNAME_FIELD] = CharField()

    def validate(self, attrs):
        self.user = authenticate(
            request=self.context.get("request"),
            username=attrs.get(User.USERNAME_FIELD),
            password=attrs.get("password"),
        )

        if not getattr(self.user, api_settings.USER_ACTIVE_FIELD, True):
            raise UserAccountDisabledError()

        if not self.user:
            raise UnauthenticatedError()

        return {}


class CodeLoginSerializer(RequestBodyValidator):
    """
    Validates given token and OTP code.
    """

    _FIELD_EPHEMERAL_TOKEN = "ephemeral_token"
    _FIELD_CODE = "code"

    ephemeral_token = CharField()
    code = CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def validate(self, attrs):
        ephemeral_token = attrs.get(self._FIELD_EPHEMERAL_TOKEN)
        code = attrs.get(self._FIELD_CODE)

        self.user = user_token_generator.check_token(user=None, token=ephemeral_token)
        if not self.user:
            raise InvalidTokenError()

        for auth_method in self.user.mfa_methods.filter(is_active=True):
            validated_backup_code = validate_backup_code(
                code,
                auth_method.backup_codes,
            )
            if validate_code(code, auth_method):
                return attrs
            if validated_backup_code:
                auth_method.remove_backup_code(validated_backup_code)
                return attrs
        raise InvalidCodeError()


class UserMFAMethodSerializer(ModelSerializer):
    class Meta:
        model = MFAMethod
        fields = ("name", "is_primary")


class ChangePrimaryMethodValidator(ProtectedActionValidator):
    method = ChoiceField(choices=MFA_METHODS)

    @staticmethod
    def _validate_mfa_method(mfa: MFAMethod):
        pass
