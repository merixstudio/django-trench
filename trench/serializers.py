from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db import models as django_models
from django.db.utils import DatabaseError
from django.utils.translation import ugettext as _

from rest_framework import fields, serializers

from trench.settings import api_settings
from trench.utils import (
    create_secret,
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
MFA_METHODS = [
    (k, v.get('VERBOSE_NAME', _(k))) for k, v in mfa_methods_items
]


class RequestMFAMethodActivationSerializer(serializers.Serializer):
    serializer_field_mapping = {
        django_models.AutoField: fields.IntegerField,
        django_models.BigIntegerField: fields.IntegerField,
        django_models.BooleanField: fields.BooleanField,
        django_models.CharField: fields.CharField,
        django_models.CommaSeparatedIntegerField: fields.CharField,
        django_models.DateField: fields.DateField,
        django_models.DateTimeField: fields.DateTimeField,
        django_models.DecimalField: fields.DecimalField,
        django_models.EmailField: fields.EmailField,
        django_models.Field: fields.ModelField,
        django_models.FileField: fields.FileField,
        django_models.FloatField: fields.FloatField,
        django_models.ImageField: fields.ImageField,
        django_models.IntegerField: fields.IntegerField,
        django_models.NullBooleanField: fields.NullBooleanField,
        django_models.PositiveIntegerField: fields.IntegerField,
        django_models.PositiveSmallIntegerField: fields.IntegerField,
        django_models.SlugField: fields.SlugField,
        django_models.SmallIntegerField: fields.IntegerField,
        django_models.TextField: fields.CharField,
        django_models.TimeField: fields.TimeField,
        django_models.URLField: fields.URLField,
        django_models.GenericIPAddressField: fields.IPAddressField,
        django_models.FilePathField: fields.FilePathField,
    }

    default_error_messages = {
        'required_field_missing':
        _('Required field not provided'),
        'required_field_update_failed':
        _('Failed to update required User data. Try again.')
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        context = kwargs['context']

        self.user = context['request'].user
        self.conf = api_settings.MFA_METHODS[context['name']]

        self.source_field = self.conf.get('SOURCE_FIELD')
        if self.source_field:
            value, field_name, klass = get_nested_attr(
                self.user, self.source_field)
            if not value:
                self.fields[field_name] = (
                    self.get_serializer_field_mapping()[klass](
                        required=True)
                )
                self.required_field_name = field_name

    def validate(self, attrs):
        if hasattr(self, 'required_field_name'):
            if self.required_field_name in attrs:
                try:
                    set_nested_attr(
                        self.user,
                        self.source_field,
                        attrs[self.required_field_name],
                    )
                except (AttributeError, DatabaseError):  # pragma: no cover
                    self.fail('required_field_update_failed')  # pragma: no cover  # noqa
            else:  # pragma: no cover
                self.fail('required_field_missing')  # pragma: no cover

        return attrs

    def create(self, validated_data):
        """
        Creates new MFAMethod object for given user, sets it as inactive,
        and marks as primary if no other active MFAMethod exists for user.
        """
        return MFAMethod.objects.get_or_create(
            user=self.user,
            name=self.context['name'],
            defaults={
                'secret': create_secret(),
                'is_active': False,
            }
        )

    def get_serializer_field_mapping(self):
        return self.serializer_field_mapping


class ProtectedActionSerializer(serializers.Serializer):
    requires_mfa_code = None
    code = serializers.CharField(
        required=False,
    )

    default_error_messages = {
        'otp_code_missing': _('OTP code not provided.'),
        'code_invalid_or_expired': _('Code invalid or expired.'),
    }

    def _validate_code(self, value):
        if not value:
            self.fail('otp_code_missing')

        obj = self.context['obj']
        validity_period = (
            self.context['conf'].get('VALIDITY_PERIOD')
            or api_settings.DEFAULT_VALIDITY_PERIOD  # noqa
        )
        validated_backup_code = validate_backup_code(value, obj.backup_codes)
        if validate_code(value, obj, validity_period):
            return value
        if validated_backup_code:
            obj.remove_backup_code(validated_backup_code)
            return value

        self.fail('code_invalid_or_expired')

    def validate(self, data):
        if self.requires_mfa_code:
            self._validate_code(data.get('code'))

        return super().validate(data)


class RequestMFAMethodActivationConfirmSerializer(ProtectedActionSerializer):
    requires_mfa_code = True


class RequestMFAMethodDeactivationSerializer(ProtectedActionSerializer):
    requires_mfa_code = api_settings.CONFIRM_DISABLE_WITH_CODE

    default_error_messages = {
        'code_invalid_or_expired': _('Code invalid or expired.'),
        'new_primary_same_as_old':
        _(
            'MFA Method to be deactivated cannot be chosen'
            ' as new primary method.'
        ),
        'method_not_registered_for_user':
        _(
            'Selected new primary MFA method'
            ' is not registered for current user.'
        ),
        'new_primary_method_inactive':
        _('MFA Method selected as new primary method is not active'),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        context = kwargs['context']
        self.user = context['request'].user

        is_current_method_primary = (
            MFAMethod.objects
            .filter(user=self.user, name=context['name'])
            .get()
            .is_primary
        )

        self.users_active_methods_count = (
            MFAMethod.objects
            .filter(user=self.user, is_active=True)
            .count()
        )
        if is_current_method_primary and self.users_active_methods_count > 2:
            self.fields['new_primary_method'] = serializers.CharField(
                max_length=255, required=True)
        else:
            self.new_method = None

    def validate_new_primary_method(self, value):
        method_to_deactivate = self.context.get('name')

        if method_to_deactivate == value:
            self.fail('new_primary_same_as_old')

        try:
            self.new_method = MFAMethod.objects.get(user=self.user, name=value)
        except MFAMethod.DoesNotExist:
            self.fail('method_not_registered_for_user')
        if not self.new_method.is_active:
            self.fail('new_primary_method_inactive')  # pragma: no cover
        return value


class RequestMFAMethodBackupCodesRegenerationSerializer(
    ProtectedActionSerializer
):
    requires_mfa_code = api_settings.CONFIRM_BACKUP_CODES_REGENERATION_WITH_CODE  # noqa


class RequestMFAMethodCodeSerializer(serializers.Serializer):
    method = serializers.CharField(
        max_length=255,
        required=False,
    )

    default_error_messages = {
        'mfa_method_not_exists': _('Requested MFA method does not exists'),
    }

    def validate_method(self, value):
        if value and value not in api_settings.MFA_METHODS:
            self.fail('mfa_method_not_exists')
        return value


class LoginSerializer(serializers.Serializer):
    """
    Validates user's credentials.
    """
    password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True,
    )

    def __init__(self, *args, **kwargs):
        super(LoginSerializer, self).__init__(*args, **kwargs)
        self.user = None
        self.fields[User.USERNAME_FIELD] = serializers.CharField()

    def validate(self, attrs):
        self.user = authenticate(
            request=self.context.get('request'),
            username=attrs.get(User.USERNAME_FIELD),
            password=attrs.get('password')
        )

        if not getattr(self.user, api_settings.USER_ACTIVE_FIELD, True):
            msg = _('User account is disabled.')  # pragma: no cover
            raise serializers.ValidationError(msg)  # pragma: no cover

        if not self.user:
            msg = _('Unable to login with provided credentials.')
            raise serializers.ValidationError(msg)

        return {}


class CodeLoginSerializer(serializers.Serializer):
    """
    Validates given token and OTP code.
    """
    ephemeral_token = serializers.CharField()
    code = serializers.CharField()

    default_error_messages = {
        'invalid_token': _('Invalid or expired token.'),
        'invalid_code': _('Invalid or expired code.'),
    }

    def validate(self, attrs):
        ephemeral_token = attrs.get('ephemeral_token')
        code = attrs.get('code')

        self.user = user_token_generator.check_token(ephemeral_token)
        if not self.user:
            self.fail('invalid_token')

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

        self.fail('invalid_code')


class UserMFAMethodSerializer(serializers.ModelSerializer):
    """
    Serializes active MFA method for user preview
    """
    class Meta:
        model = MFAMethod
        fields = ('name', 'is_primary')


class ChangePrimaryMethodSerializer(serializers.Serializer):
    """
    Serializes request to change default authentication method.
    """
    code = serializers.CharField()
    method = serializers.ChoiceField(choices=MFA_METHODS)

    default_error_messages = {
        'not_enabled': _('2FA is not enabled.'),
        'invalid_code': _('Invalid or expired code.'),
        'missing_method': _('Target method does not exist or is not active'),
    }

    def validate(self, attrs):
        user = self.context.get('request').user
        try:
            current_method = user.mfa_methods.get(
                is_primary=True,
                is_active=True,
            )
        except ObjectDoesNotExist:
            self.fail('not_enabled')
        try:
            new_primary_method = user.mfa_methods.get(
                name=attrs.get('method'),
                is_active=True,
            )
        except ObjectDoesNotExist:
            self.fail('missing_method')
        code = attrs.get('code')
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
            self.fail('invalid_code')

    def save(self):
        new_method = self.validated_data.get('new_method')
        old_method = self.validated_data.get('old_method')
        new_method.is_primary = True
        old_method.is_primary = False
        new_method.save()
        old_method.save()
