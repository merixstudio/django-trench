from django.conf import LazySettings, settings
from django.utils.module_loading import import_string

from functools import cached_property
from typing import Any, Dict

from trench.domain.models import TrenchConfig
from trench.exceptions import MethodHandlerMissingError


SOURCE_FIELD = "source_field"
HANDLER = "handler"
VALIDITY_PERIOD = "validity_period"
VERBOSE_NAME = "varbose_name"
EMAIL_SUBJECT = "email_subject"
EMAIL_PLAIN_TEMPLATE = "email_plain_template"
EMAIL_HTML_TEMPLATE = "email_html_template"
SMSAPI_ACCESS_TOKEN = "smsapi_access_token"
SMSAPI_FROM_NUMBER = "smsapi_from_number"
TWILIO_VERIFIED_FROM_NUMBER = "twilio_verified_from_number"
YUBICLOUD_CLIENT_ID = "yubicloud_client_id"
AWS_ACCESS_KEY = "aws_access_key"
AWS_SECRET_KEY = "aws_secret_key"
AWS_REGION = "aws_region"
MFA_METHODS_CONFIGS = {
    "email": "trench.domain.models.MFAMethodConfigEmail",
    "app": "trench.domain.models.MFAMethodConfigApp",
    "sms_twilio": "trench.domain.models.MFAMethodConfigTwilio",
    "sms_api": "trench.domain.models.MFAMethodConfigSMSAPI",
    "sms_aws": "trench.domain.models.MFAMethodConfigAws",
    "yubi": "trench.domain.models.MFAMethodConfigYubi",
}


class TrenchSettingsParser:
    _FIELD_TRENCH_AUTH = "TRENCH_AUTH"
    _FIELD_MFA_METHODS = "MFA_METHODS"
    _FIELD_HANDLER = "handler"

    def __init__(self, user_settings: LazySettings):
        self._user_settings = getattr(user_settings, self._FIELD_TRENCH_AUTH, {})

    @cached_property
    def get_settings(self) -> TrenchConfig:
        trench_settings_dict = {}

        for field in TrenchConfig.__dataclass_fields__:
            field_name = str(field)
            if field_name == "mfa_methods":
                mfa_methods: Dict[str, Dict[str, Any]] = {}
                custom_mfa_methods = self._user_settings.get(field_name.upper(), None)
                if custom_mfa_methods:
                    for (
                        mfa_method_name,
                        mfa_method_values,
                    ) in custom_mfa_methods.items():  # noqa: E501
                        mfa_methods[mfa_method_name] = {}
                        for (
                            mfa_method_value_key,
                            mfa_method_value,
                        ) in mfa_method_values.items():  # noqa: E501
                            mfa_methods[mfa_method_name][
                                mfa_method_value_key.lower()
                            ] = mfa_method_value  # noqa: E501
                        if self._FIELD_HANDLER not in mfa_methods[mfa_method_name]:
                            raise MethodHandlerMissingError(method_name=mfa_method_name)
                else:
                    for (
                        mfa_method_name,
                        mfa_method_config,
                    ) in MFA_METHODS_CONFIGS.items():  # noqa: E501
                        mfa_method = import_string(mfa_method_config)
                        mfa_methods[mfa_method_name] = {}
                        for mfa_method_field_name in mfa_method.__dataclass_fields__:
                            mfa_methods[mfa_method_name][
                                mfa_method_field_name
                            ] = getattr(  # noqa: E501
                                mfa_method, mfa_method_field_name, None
                            )
                trench_settings_dict[field_name] = mfa_methods

            else:
                trench_settings_dict[field_name] = self._user_settings.get(
                    field_name.upper(), getattr(TrenchConfig, field_name)
                )

        return TrenchConfig(**trench_settings_dict)  # type: ignore


trench_settings = TrenchSettingsParser(user_settings=settings).get_settings
