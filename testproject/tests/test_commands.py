import pytest

from trench.command.deactivate_mfa_method import deactivate_mfa_method_command
from trench.command.remove_backup_code import (
    RemoveBackupCodeCommand,
    remove_backup_code_command,
)
from trench.exceptions import MFAMethodDoesNotExistError, MFANotEnabledError
from trench.settings import DEFAULTS, TrenchAPISettings
from trench.utils import get_mfa_model


@pytest.mark.django_db
def test_remove_backup_code_from_non_existing_method(
    active_user_with_application_otp, settings
):
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
    remove_backup_code_command = RemoveBackupCodeCommand(
        mfa_model=get_mfa_model(), settings=settings
    ).execute
    code = next(iter(codes))
    remove_backup_code_command(
        user_id=user.id,
        method_name="email",
        code=code,
    )


@pytest.mark.django_db
def test_deactivate_inactive_mfa(active_user_with_application_otp):
    mfa_method = active_user_with_application_otp.mfa_methods.get(name="app")
    mfa_method.is_active = False
    mfa_method.is_primary = False
    mfa_method.save()
    with pytest.raises(MFANotEnabledError):
        deactivate_mfa_method_command(
            user_id=active_user_with_application_otp.id,
            mfa_method_name=mfa_method.name,
        )


@pytest.mark.django_db
def test_deactivate_an_only_mfa_method(active_user_with_application_otp):
    mfa_method = active_user_with_application_otp.mfa_methods.get(name="app")
    deactivate_mfa_method_command(
        user_id=active_user_with_application_otp.id,
        mfa_method_name=mfa_method.name,
    )
    mfa_model = get_mfa_model()
    mfa_method.refresh_from_db()
    assert mfa_method.is_active is False
    assert len(mfa_model.objects.list_active(user_id=active_user_with_application_otp.id)) == 0

