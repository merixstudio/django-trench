import pyotp

from trench.exceptions import MissingSourceFieldAttribute
from trench.settings import api_settings
from trench.utils import create_otp_code, get_nested_attr_value


class AbstractMessageDispatcher:
    def __init__(self, user, obj, conf):
        self.user = user
        self.obj = obj
        self.conf = conf
        self.to = ''

        if 'SOURCE_FIELD' in conf:
            value = get_nested_attr_value(user, conf['SOURCE_FIELD'])
            if not value:
                raise MissingSourceFieldAttribute(  # pragma: no cover
                    'Could not retrieve attribute '
                    '{} for given user'.format(conf['SOURCE_FIELD'])
                )
            self.to = value

    def dispatch_message(self):
        pass  # pragma: no cover

    def create_code(self):
        return create_otp_code(self.obj.secret)

    def confirm_activation(self, code):
        pass

    def validate_confirmation_code(self, code):
        return self.validate_code(code)

    def validate_code(self, code):
        validity_period = self.conf.get('VALIDITY_PERIOD') or \
            api_settings.DEFAULT_VALIDITY_PERIOD
        return pyotp.TOTP(self.obj.secret).verify(
            code,
            valid_window=int(validity_period / 30)
        )
