from django.conf import settings
from django.utils.translation import gettext_lazy as _

import string
from rest_framework.settings import APISettings, perform_import
from typing import Any

from trench.exceptions import (
    MethodHandlerMissingError,
    RestrictedCharInBackupCodeError,
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
        val = super().__getattr__(attr)
        self._validate(attribute=attr, value=val)
        return val

    def _validate(self, attribute: str, value: Any):
        if attribute == self._FIELD_BACKUP_CODES_CHARACTERS:
            if any(char in value for char in self._RESTRICTED_BACKUP_CODES_CHARACTERS):
                raise RestrictedCharInBackupCodeError(
                    attribute_name=attribute,
                    restricted_chars=self._RESTRICTED_BACKUP_CODES_CHARACTERS,
                )
        if attribute == self._FIELD_MFA_METHODS:
            for method_name, method_config in value.items():
                if self._FIELD_HANDLER not in method_config:
                    raise MethodHandlerMissingError(method_name=method_name)
                for k, v in self.defaults[self._FIELD_MFA_METHODS][method_name].items():
                    method_config[k] = method_config.get(k, v)
                method_config[self._FIELD_HANDLER] = perform_import(
                    method_config[self._FIELD_HANDLER], self._FIELD_HANDLER
                )

    def __getitem__(self, attr):
        return self.__getattr__(attr)


SOURCE_FIELD = "SOURCE_FIELD"
HANDLER = "HANDLER"
VALIDITY_PERIOD = "VALIDITY_PERIOD"
VERBOSE_NAME = "VERBOSE_NAME"
EMAIL_SUBJECT = "EMAIL_SUBJECT"
EMAIL_PLAIN_TEMPLATE = "EMAIL_PLAIN_TEMPLATE"
EMAIL_HTML_TEMPLATE = "EMAIL_HTML_TEMPLATE"
SMSAPI_ACCESS_TOKEN = "SMSAPI_ACCESS_TOKEN"
SMSAPI_FROM_NUMBER = "SMSAPI_FROM_NUMBER"
TWILIO_VERIFIED_FROM_NUMBER = "TWILIO_VERIFIED_FROM_NUMBER"
YUBICLOUD_CLIENT_ID = "YUBICLOUD_CLIENT_ID"

DEFAULTS = {
    "USER_MFA_MODEL": "trench.MFAMethod",
    "USER_ACTIVE_FIELD": "is_active",
    "BACKUP_CODES_QUANTITY": 5,
    "BACKUP_CODES_LENGTH": 12,  # keep (quantity * length) under 200
    "BACKUP_CODES_CHARACTERS": (string.ascii_letters + string.digits),
    "SECRET_KEY_LENGTH": 32,
    "DEFAULT_VALIDITY_PERIOD": 30,
    "CONFIRM_DISABLE_WITH_CODE": False,
    "CONFIRM_BACKUP_CODES_REGENERATION_WITH_CODE": True,
    "ALLOW_BACKUP_CODES_REGENERATION": True,
    "ENCRYPT_BACKUP_CODES": True,
    "APPLICATION_ISSUER_NAME": "MyApplication",
    "MFA_METHODS": {
        "sms_twilio": {
            VERBOSE_NAME: _("sms_twilio"),
            VALIDITY_PERIOD: 60 * 10,
            HANDLER: "trench.backends.twilio.TwilioMessageDispatcher",
            SOURCE_FIELD: "phone_number",
            TWILIO_VERIFIED_FROM_NUMBER: "YOUR TWILIO REGISTERED NUMBER",
        },
        "sms_api": {
            VERBOSE_NAME: _("sms_api"),
            VALIDITY_PERIOD: 60 * 10,
            HANDLER: "trench.backends.sms_api.SMSAPIMessageDispatcher",
            SOURCE_FIELD: "phone_number",
            SMSAPI_ACCESS_TOKEN: "YOUR SMSAPI TOKEN",
            SMSAPI_FROM_NUMBER: "YOUR REGISTERED NUMBER",
        },
        "email": {
            VERBOSE_NAME: _("email"),
            VALIDITY_PERIOD: 60 * 10,
            HANDLER: "trench.backends.basic_mail.SendMailMessageDispatcher",
            SOURCE_FIELD: "email",
            EMAIL_SUBJECT: _("Your verification code"),
            EMAIL_PLAIN_TEMPLATE: "trench/backends/email/code.txt",
            EMAIL_HTML_TEMPLATE: "trench/backends/email/code.html",
        },
        "app": {
            VERBOSE_NAME: _("app"),
            VALIDITY_PERIOD: 60 * 10,
            "USES_THIRD_PARTY_CLIENT": True,
            HANDLER: "trench.backends.application.ApplicationMessageDispatcher",
        },
        "yubi": {
            VERBOSE_NAME: _("yubi"),
            HANDLER: "trench.backends.yubikey.YubiKeyMessageDispatcher",
            YUBICLOUD_CLIENT_ID: "YOUR KEY",
        },
    },
}

trench_settings = TrenchAPISettings(
    user_settings=None, defaults=DEFAULTS, import_strings=None
)
