from django.utils.translation import gettext_lazy as _

import string
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class MFAMethodConfig:
    verbose_name: str
    handler: str
    validity_period: Optional[int] = None
    source_field: Optional[str] = None


@dataclass(frozen=True)
class TrenchConfig:
    mfa_methods: Dict[str, Any] = field(default_factory=dict)
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


@dataclass(frozen=True)
class MFAMethodConfigAws(MFAMethodConfig):
    verbose_name = _("sms_aws")
    handler = "trench.backends.aws.AWSMessageDispatcher"
    validity_period = 30
    source_field = "phone_number"
    aws_access_key = "access_key"
    aws_secret_key = "secret_key"
    aws_region = "region"


@dataclass(frozen=True)
class MFAMethodConfigApp(MFAMethodConfig):
    verbose_name = _("app")
    validity_period = 30
    handler = "trench.backends.application.ApplicationMessageDispatcher"
    uses_third_party_client: bool = True


@dataclass(frozen=True)
class MFAMethodConfigEmail(MFAMethodConfig):
    verbose_name = _("email")
    validity_period = 30
    handler = "trench.backends.basic_mail.SendMailMessageDispatcher"
    source_field = "email"
    email_subject: str = _("Your verification code")
    email_plain_template: str = "trench/backends/email/code.txt"
    email_html_template: str = "trench/backends/email/code.html"


@dataclass(frozen=True)
class MFAMethodConfigYubi(MFAMethodConfig):
    verbose_name = _("yubi")
    handler = "trench.backends.yubikey.YubiKeyMessageDispatcher"
    yubicloud_client_id: str = "YOUR KEY"


@dataclass(frozen=True)
class MFAMethodConfigTwilio(MFAMethodConfig):
    verbose_name = _("sms_twilio")
    validity_period = 30
    handler = "trench.backends.twilio.TwilioMessageDispatcher"
    source_field = "phone_number"
    twilio_verified_from_number: str = ""


@dataclass(frozen=True)
class MFAMethodConfigSMSAPI(MFAMethodConfig):
    verbose_name = _("sms_api")
    validity_period = 30
    handler = "trench.backends.sms_api.SMSAPIMessageDispatcher"
    source_field = "phone_number"
    smsapi_access_token: str = ""
    smsapi_from_number: str = ""
