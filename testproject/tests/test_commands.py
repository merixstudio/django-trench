import pytest

from trench.command.remove_backup_code import remove_backup_code_command, RemoveBackupCodeCommand
from trench.exceptions import MFAMethodDoesNotExistError
from trench.settings import TrenchAPISettings, DEFAULTS
from trench.utils import get_mfa_model


@pytest.mark.django_db
def test_remove_backup_code_from_non_existing_method(active_user_with_application_otp, settings):
    with pytest.raises(MFAMethodDoesNotExistError):
        remove_backup_code_command(
            user_id=active_user_with_application_otp.id,
            method_name="non_existing_name",
            code="whatever",
        )


@pytest.mark.django_db
def test_remove_not_encrypted_code(active_user_with_non_encrypted_backup_codes):
    user, codes = active_user_with_non_encrypted_backup_codes
    settings = TrenchAPISettings(
        user_settings={"ENCRYPT_BACKUP_CODES": False}, defaults=DEFAULTS
    )
    remove_backup_code_command = RemoveBackupCodeCommand(mfa_model=get_mfa_model(), settings=settings).execute
    code = next(iter(codes))
    remove_backup_code_command(
        user_id=user.id,
        method_name="email",
        code=code,
    )
