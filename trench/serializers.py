from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import DatabaseError
from django.utils.translation import gettext as _

from collections import OrderedDict
from rest_framework.fields import CharField, ChoiceField
from rest_framework.serializers import ModelSerializer, Serializer

from trench.exceptions import (
    CodeInvalidOrExpiredValidationError,
    InvalidCodeValidationError,
    InvalidTokenValidationError,
    MFAMethodDoesNotExistValidationError,
    MFAMethodNotRegisteredForUserValidationError,
    MFANewPrimarySameAsOldValidationError,
    MFANotEnabledValidationError,
    MFAPrimaryMethodInactiveValidationError,
    OTPCodeMissingValidationError,
    RequiredFieldMissingValidationError,
    RequiredFieldUpdateFailedValidationError,
    UnauthenticatedValidationError,
    UserAccountDisabledValidationError,
)
from trench.settings import api_settings
from trench.utils import (
    create_secret,
    get_mfa_handler,
    get_mfa_model,
    get_nested_attr,
    set_nested_attr,
    user_token_generator,
    validate_backup_code,
    validate_code,
)


User = get_user_model()
MFAMethod = get_mfa_model()

mfa_methods_items = api_settings.MFA_METHODS.items()
MFA_METHODS = [(k, v.get("VERBOSE_NAME", _(k))) for k, v in mfa_methods_items]


class RequestValidator(Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class RequestMFAMethodActivationSerializer(Serializer):
    serializer_field_mapping = ModelSerializer.serializer_field_mapping

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        context = kwargs["context"]

        self.user = context["request"].user
        self.conf = api_settings.MFA_METHODS[context["name"]]
        self.source_field = self.conf.get("SOURCE_FIELD")
        if self.source_field:
            value, field_name, klass = get_nested_attr(self.user, self.source_field)
            if not value:
                self.fields[field_name] = self.get_serializer_field_mapping()[klass](
                    required=True
                )
                self.required_field_name = field_name

    def validate(self, attrs):
        if hasattr(self, "required_field_name"):
            if self.required_field_name in attrs:
                try:
                    set_nested_attr(
                        self.user,
                        self.source_field,
                        attrs[self.required_field_name],
                    )
                except (AttributeError, DatabaseError):
                    raise RequiredFieldUpdateFailedValidationError()
            else:
                raise RequiredFieldMissingValidationError()

        return attrs

    def create(self, validated_data: OrderedDict) -> MFAMethod:
        """
        Creates new MFAMethod object for given user, sets it as inactive,
        and marks as primary if no other active MFAMethod exists for user.
        """
        return MFAMethod.objects.get_or_create(
            user=self.user,
            name=self.context["name"],
            defaults={
                "secret": create_secret(),
                "is_active": False,
            },
        )

    def update(self, instance: MFAMethod, validated_data: OrderedDict):
        pass

    def get_serializer_field_mapping(self):
        return self.serializer_field_mapping


class ProtectedActionSerializer(Serializer):
    requires_mfa_code = None
    handler_validation_method = "validate_code"

    code = CharField(required=False)

    def _validate_code(self, value: str) -> str:
        if not value:
            raise OTPCodeMissingValidationError()

        obj = self.context["obj"]
        validated_backup_code = validate_backup_code(value, obj.backup_codes)
        handler = get_mfa_handler(obj)
        validate_method = getattr(handler, self.handler_validation_method)
        if validate_method(value):
            return value
        if validated_backup_code:
            obj.remove_backup_code(validated_backup_code)
            return value
        raise CodeInvalidOrExpiredValidationError()

    def validate(self, data):
        if self.requires_mfa_code:
            self._validate_code(data.get("code"))

        return super().validate(data)

    def create(self, validated_data: OrderedDict):
        pass

    def update(self, instance, validated_data: OrderedDict):
        pass


class RequestMFAMethodActivationConfirmSerializer(ProtectedActionSerializer):
    requires_mfa_code = True
    handler_validation_method = "validate_confirmation_code"


class RequestMFAMethodDeactivationSerializer(ProtectedActionSerializer):
    requires_mfa_code = api_settings.CONFIRM_DISABLE_WITH_CODE

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        context = kwargs["context"]
        self.user = context["request"].user

        is_current_method_primary = (
            MFAMethod.objects.filter(user=self.user, name=context["name"])
            .values_list("is_primary", flat=True)
            .first()
        )

        self.users_active_methods_count = MFAMethod.objects.filter(
            user=self.user, is_active=True
        ).count()
        if is_current_method_primary and self.users_active_methods_count > 2:
            self.fields["new_primary_method"] = CharField(max_length=255, required=True)
        else:
            self.new_method = None

    def validate_new_primary_method(self, value):
        method_to_deactivate = self.context.get("name")

        if method_to_deactivate == value:
            raise MFANewPrimarySameAsOldValidationError()

        try:
            self.new_method = MFAMethod.objects.get(user=self.user, name=value)
        except MFAMethod.DoesNotExist:
            raise MFAMethodNotRegisteredForUserValidationError()
        if not self.new_method.is_active:
            raise MFAPrimaryMethodInactiveValidationError()
        return value


class RequestMFAMethodBackupCodesRegenerationSerializer(ProtectedActionSerializer):
    requires_mfa_code = api_settings.CONFIRM_BACKUP_CODES_REGENERATION_WITH_CODE  # noqa


class RequestMFAMethodCodeSerializer(RequestValidator):
    method = CharField(max_length=255, required=False)

    @staticmethod
    def validate_method(value: str) -> str:
        if value and value not in api_settings.MFA_METHODS:
            raise MFAMethodDoesNotExistValidationError()
        return value


class LoginSerializer(RequestValidator):
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
            raise UserAccountDisabledValidationError()

        if not self.user:
            raise UnauthenticatedValidationError()

        return {}


class CodeLoginSerializer(RequestValidator):
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
            raise InvalidTokenValidationError()

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
        raise InvalidCodeValidationError()


class UserMFAMethodSerializer(ModelSerializer):
    """
    Serializes active MFA method for user preview
    """

    class Meta:
        model = MFAMethod
        fields = ("name", "is_primary")


class ChangePrimaryMethodSerializer(RequestValidator):
    """
    Serializes request to change default authentication method.
    """

    code = CharField()
    method = ChoiceField(choices=MFA_METHODS)

    def validate(self, attrs):
        user = self.context.get("request").user
        try:
            current_method = user.mfa_methods.get(
                is_primary=True,
                is_active=True,
            )
        except ObjectDoesNotExist:
            raise MFANotEnabledValidationError()
        try:
            new_primary_method = user.mfa_methods.get(
                name=attrs.get("method"),
                is_active=True,
            )
        except ObjectDoesNotExist:
            raise MFAMethodDoesNotExistValidationError()
        code = attrs.get("code")
        validated_backup_code = validate_backup_code(
            code,
            current_method.backup_codes,
        )
        if validate_code(code, current_method):
            attrs.update(new_method=new_primary_method)
            attrs.update(old_method=current_method)
            return attrs
        elif validated_backup_code:
            attrs.update(new_method=new_primary_method)
            attrs.update(old_method=current_method)
            current_method.remove_backup_code(validated_backup_code)
            return attrs
        else:
            raise InvalidCodeValidationError()

    def save(self):
        new_method = self.validated_data.get("new_method")
        old_method = self.validated_data.get("old_method")
        new_method.is_primary = True
        old_method.is_primary = False
        new_method.save()
        old_method.save()
