from django.contrib.auth.hashers import make_password

from typing import List
from typing_extensions import Type

from trench.exceptions import MFAMethodDoesNotExistError
from trench.models import MFAMethod
from trench.query.get_mfa_method import get_mfa_method
from trench.query.primary_mfa_method_exists import primary_mfa_method_exists_query
from trench.settings import api_settings
from trench.utils import generate_backup_codes, get_mfa_handler, get_mfa_model


class ActivateMFAMethodCommand:
    def __init__(self, requires_encryption: bool, mfa_model: Type[MFAMethod]):
        self._requires_encryption = requires_encryption
        self._mfa_model = mfa_model

    def execute(self, user_id: int, name: str, code: str) -> List[str]:
        mfa = get_mfa_method(user_id=user_id, name=name)
        handler = get_mfa_handler(mfa)
        handler.confirm_activation(code)

        backup_codes = generate_backup_codes()

        rows_affected = self._mfa_model.objects.filter(
            user_id=user_id, name=name
        ).update(
            _backup_codes=[make_password(backup_code) for backup_code in backup_codes]
            if self._requires_encryption
            else backup_codes,
            is_active=True,
            is_primary=not primary_mfa_method_exists_query(user_id=user_id),
        )

        if rows_affected < 1:
            raise MFAMethodDoesNotExistError()

        return backup_codes


activate_mfa_method_command = ActivateMFAMethodCommand(
    requires_encryption=api_settings.ENCRYPT_BACKUP_CODES, mfa_model=get_mfa_model()
).execute
