from dataclasses import dataclass
from functools import cached_property

from django.conf import settings, LazySettings
from django.utils.translation import gettext_lazy as _

import string
from rest_framework.settings import APISettings, perform_import
from typing import Any, Dict, Optional

from trench.exceptions import MethodHandlerMissingError


@dataclass(frozen=True)
class MFAMethodConfig:
    verbose_name: str
    validity_period: int
    handler: str
    source_field: Optional[str] = None


@dataclass(frozen=True)
class TrenchConfig:
    mfa_methods: Dict[str, MFAMethodConfig]
    user_mfa_model: str = "trench.MFAMethod"
    user_active_field: str = "is_active"
    backup_codes_quantity: int = 5
    backup_codes_length: int = 12
    backup_codes_characters: str = string.ascii_letters + string.digits
    secret_key_length: int = 32
    default_validity_period: int = 30
    confirm_disable_with_code: bool = False
    confirm_backup_codes_regeneration_with_code: bool = True
    allow_backup_codes_regeneration: bool = True
    encrypt_backup_codes: bool = True
    application_issuer_name: str = "MyApplication"


class TrenchSettingsParser:
    _FIELD_TRENCH_AUTH = "TRENCH_AUTH"

    def __init__(self, user_settings: LazySettings):
        self._user_settings = getattr(user_settings, self._FIELD_TRENCH_AUTH, {})

    @cached_property
    def get_settings(self) -> TrenchConfig:
        settings = {}
        for field in TrenchConfig.__dataclass_fields__:
            field_name = str(field)
            if field_name == "mfa_methods":
                pass  # TODO: perform backend import
            else:
                settings[field_name] = getattr(self._user_settings, field_name, getattr(TrenchConfig, field_name))
        return TrenchConfig(**settings)


class TrenchAPISettings(APISettings):
    _FIELD_USER_SETTINGS = "_user_settings"
    _FIELD_TRENCH_AUTH = "TRENCH_AUTH"
    _FIELD_BACKUP_CODES_CHARACTERS = "BACKUP_CODES_CHARACTERS"
    _FIELD_MFA_METHODS = "MFA_METHODS"
    _FIELD_HANDLER = "HANDLER"

    @property
    def user_settings(self) -> Dict[str, Any]:
        if not hasattr(self, self._FIELD_USER_SETTINGS):
            self._user_settings = getattr(settings, self._FIELD_TRENCH_AUTH, {})
        return self._user_settings

    def __getattr__(self, attr: str) -> Any:
        val = super().__getattr__(attr)
        self._validate(attribute=attr, value=val)
        return val

    def _validate(self, attribute: str, value: Any) -> None:
        if attribute == self._FIELD_MFA_METHODS:
            for method_name, method_config in value.items():
                if self._FIELD_HANDLER not in method_config:
                    raise MethodHandlerMissingError(method_name=method_name)
                for k, v in self.defaults[self._FIELD_MFA_METHODS][method_name].items():
                    method_config[k] = method_config.get(k, v)
                method_config[self._FIELD_HANDLER] = perform_import(
                    method_config[self._FIELD_HANDLER], self._FIELD_HANDLER
                )

    def __getitem__(self, attr: str) -> Any:
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
AWS_ACCESS_KEY = "AWS_ACCESS_KEY"
AWS_SECRET_KEY = "AWS_SECRET_KEY"
AWS_REGION = "AWS_REGION"

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
            VALIDITY_PERIOD: 30,
            HANDLER: "trench.backends.twilio.TwilioMessageDispatcher",
            SOURCE_FIELD: "phone_number",
            TWILIO_VERIFIED_FROM_NUMBER: "YOUR TWILIO REGISTERED NUMBER",
        },
        "sms_api": {
            VERBOSE_NAME: _("sms_api"),
            VALIDITY_PERIOD: 30,
            HANDLER: "trench.backends.sms_api.SMSAPIMessageDispatcher",
            SOURCE_FIELD: "phone_number",
            SMSAPI_ACCESS_TOKEN: "YOUR SMSAPI TOKEN",
            SMSAPI_FROM_NUMBER: "YOUR REGISTERED NUMBER",
        },
        "sms_aws": {
            VERBOSE_NAME: _("sms_aws"),
            VALIDITY_PERIOD: 30,
            HANDLER: "trench.backends.aws.AWSMessageDispatcher",
            SOURCE_FIELD: "phone_number",
            AWS_ACCESS_KEY: "YOUR AWS ACCESS KEY",
            AWS_SECRET_KEY: "YOUR AWS SECRET KEY",
            AWS_REGION: "YOUR AWS REGION",
        },
        "email": {
            VERBOSE_NAME: _("email"),
            VALIDITY_PERIOD: 30,
            HANDLER: "trench.backends.basic_mail.SendMailMessageDispatcher",
            SOURCE_FIELD: "email",
            EMAIL_SUBJECT: _("Your verification code"),
            EMAIL_PLAIN_TEMPLATE: "trench/backends/email/code.txt",
            EMAIL_HTML_TEMPLATE: "trench/backends/email/code.html",
        },
        "app": {
            VERBOSE_NAME: _("app"),
            VALIDITY_PERIOD: 30,
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
