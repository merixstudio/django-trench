import string
from typing import Any

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from rest_framework.settings import APISettings, perform_import

from trench.exceptions import (
    RestrictedCharInBackupCodeError,
    MethodHandlerMissingError,
    InvalidSettingError,
)


class TrenchAPISettings(APISettings):
    _FIELD_USER_SETTINGS = "_user_settings"
    _FIELD_TRENCH_AUTH = "TRENCH_AUTH"
    _FIELD_BACKUP_CODES_CHARACTERS = "BACKUP_CODES_CHARACTERS"
    _FIELD_MFA_METHODS = "MFA_METHODS"
    _FIELD_HANDLER = "HANDLER"
    _RESTRICTED_BACKUP_CODES_CHARACTERS = (",",)

    @property
    def user_settings(self):
        if not hasattr(self, self._FIELD_USER_SETTINGS):
            self._user_settings = getattr(settings, self._FIELD_TRENCH_AUTH, {})
        return self._user_settings

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise InvalidSettingError(attribute_name=attr)
        try:
            val = self.user_settings[attr]
        except KeyError:
            val = self.defaults[attr]
        if attr in self.import_strings:
            val = perform_import(val, attr)
        self._validate(attribute=attr, value=val)
        self._cache(attribute=attr, value=val)
        return val

    @classmethod
    def _validate(cls, attribute: str, value: Any):
        if attribute == cls._FIELD_BACKUP_CODES_CHARACTERS:
            if any(char in value for char in cls._RESTRICTED_BACKUP_CODES_CHARACTERS):
                raise RestrictedCharInBackupCodeError(attribute_name=attribute)
        if attribute == cls._FIELD_MFA_METHODS:
            for method_name, method_config in value.items():
                if cls._FIELD_HANDLER not in method_config:
                    raise MethodHandlerMissingError(method_name=method_name)
                method_config[cls._FIELD_HANDLER] = perform_import(
                    method_config[cls._FIELD_HANDLER], cls._FIELD_HANDLER
                )

    def _cache(self, attribute: str, value: Any):
        self._cached_attrs.add(attribute)
        setattr(self, attribute, value)

    def __getitem__(self, attr):
        return self.__getattr__(attr)


DEFAULTS = {
    "FROM_EMAIL": getattr(settings, "DEFAULT_FROM_EMAIL"),
    "USER_MFA_MODEL": "trench.MFAMethod",
    "USER_ACTIVE_FIELD": "is_active",
    "BACKUP_CODES_QUANTITY": 5,
    "BACKUP_CODES_LENGTH": 12,  # keep (quantity * length) under 200
    "BACKUP_CODES_CHARACTERS": (string.ascii_letters + string.digits),
    "SECRET_KEY_LENGTH": 16,
    "DEFAULT_VALIDITY_PERIOD": 30,
    "CONFIRM_DISABLE_WITH_CODE": False,
    "CONFIRM_BACKUP_CODES_REGENERATION_WITH_CODE": True,
    "ALLOW_BACKUP_CODES_REGENERATION": True,
    "ENCRYPT_BACKUP_CODES": True,
    "APPLICATION_ISSUER_NAME": "MyApplication",
    "CACHE_PREFIX": "trench",
    "MAX_METHODS_PER_USER": 3,
    "MFA_METHODS": {
        "sms_twilio": {
            "VERBOSE_NAME": _("sms_twilio"),
            "VALIDITY_PERIOD": 60 * 10,
            "HANDLER": "trench.backends.twilio.TwilioBackend",
            "SOURCE_FIELD": "phone_number",
            "TWILIO_ACCOUNT_SID": "YOUR KEY",
            "TWILIO_AUTH_TOKEN": "YOUR KEY",
            "TWILIO_VERIFIED_FROM_NUMBER": "YOUR TWILIO REGISTERED NUMBER",
        },
        "sms_api": {
            "VERBOSE_NAME": _("sms_api"),
            "VALIDITY_PERIOD": 60 * 10,
            "HANDLER": "trench.backends.sms_api.SmsAPIBackend",
            "SOURCE_FIELD": "phone_number",
            "SMSAPI_ACCESS_TOKEN": "YOUR SMSAPI TOKEN",
            "SMSAPI_FROM_NUMBER": "YOUR REGISTERED NUMBER",
        },
        "email": {
            "VERBOSE_NAME": _("email"),
            "VALIDITY_PERIOD": 60 * 10,
            "HANDLER": "trench.backends.basic_mail.SendMailBackend",
            "SOURCE_FIELD": "email",
            "EMAIL_SUBJECT": _("Your verification code"),
            "EMAIL_PLAIN_TEMPLATE": "trench/backends/email/code.txt",
            "EMAIL_HTML_TEMPLATE": "trench/backends/email/code.html",
        },
        "app": {
            "VERBOSE_NAME": _("app"),
            "VALIDITY_PERIOD": 60 * 10,
            "USES_THIRD_PARTY_CLIENT": True,
            "HANDLER": "trench.backends.application.ApplicationBackend",
        },
        "yubi": {
            "VERBOSE_NAME": _("yubi"),
            "HANDLER": "trench.backends.yubikey.YubiKeyBackend",
            "YUBICLOUD_CLIENT_ID": "YOUR KEY",
        },
    },
}

api_settings = TrenchAPISettings(
    user_settings=None, defaults=DEFAULTS, import_strings=None
)
