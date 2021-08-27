from os import environ

import pytest

from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

from yubico_client import Yubico
from yubico_client.otp import OTP

from trench.command.create_secret import create_secret_command
from trench.command.generate_backup_codes import generate_backup_codes_command


User = get_user_model()


@pytest.fixture(scope="session", autouse=True)
def tests_setup_and_teardown():
    original_environment = dict(environ)
    environ.update({
        "TWILIO_ACCOUNT_SID": "TEST",
        "TWILIO_AUTH_TOKEN": "TOKEN",
    })
    yield
    environ.clear()
    environ.update(original_environment)


def mfa_method_creator(user: User, method_name: str, is_primary: bool = True, **method_args):
    MFAMethod = apps.get_model("trench.MFAMethod")
    return MFAMethod.objects.create(
        user=user,
        secret=method_args.pop("secret", create_secret_command()),
        is_primary=is_primary,
        name=method_name,
        is_active=method_args.pop("is_active", True),
        **method_args,
    )


@pytest.fixture()
def active_user_with_application_otp():
    user, created = User.objects.get_or_create(username="imhotep", email="imhotep@pyramids.eg")
    if created:
        user.set_password("secretkey")
        user.is_active = True
        user.save()
        mfa_method_creator(user=user, method_name="app")
    return user


@pytest.fixture()
def active_user_with_email_otp():
    user, created = User.objects.get_or_create(
        username="imhotep",
        email="imhotep@pyramids.eg",
    )
    if created:
        user.set_password("secretkey"),
        user.is_active = True
        user.save()
        mfa_method_creator(user=user, method_name="email")
    return user


@pytest.fixture()
def active_user_with_sms_otp():
    user, created = User.objects.get_or_create(
        username="imhotep", email="imhotep@pyramids.eg", phone_number="555-555-555"
    )
    if created:
        user.set_password("secretkey"),
        user.is_active = True
        user.save()
        mfa_method_creator(user=user, method_name="sms_api")
    return user


@pytest.fixture()
def active_user_with_twilio_otp():
    user, created = User.objects.get_or_create(
        username="imhotep", email="imhotep@pyramids.eg", phone_number="555-555-555"
    )
    if created:
        user.set_password("secretkey"),
        user.is_active = True
        user.save()
        mfa_method_creator(user=user, method_name="sms_twilio")
    return user


@pytest.fixture()
def active_user_with_email_and_inactive_other_methods_otp():
    user, created = User.objects.get_or_create(
        username="imhotep",
        email="imhotep@pyramids.eg",
    )
    if created:
        user.set_password("secretkey"),
        user.is_active = True
        user.save()
        mfa_method_creator(user=user, method_name="email")
        mfa_method_creator(user=user, method_name="sms_twilio", is_primary=False, is_active=False)
        mfa_method_creator(user=user, method_name="app", is_primary=False, is_active=False)
    return user


@pytest.fixture()
def active_user_with_backup_codes():
    user, created = User.objects.get_or_create(
        username="cleopatra",
        email="cleopatra@pyramids.eg",
    )
    backup_codes = generate_backup_codes_command()
    encrypted_backup_codes = ",".join([make_password(_) for _ in backup_codes])
    if created:
        user.set_password("secretkey"),
        user.is_active = True
        user.save()
        mfa_method_creator(user=user, method_name="email", _backup_codes=encrypted_backup_codes)
    return user, backup_codes


@pytest.fixture()
def active_user_with_many_otp_methods():
    user, created = User.objects.get_or_create(
        username="ramses",
        email="ramses@thegreat.eg",
    )
    backup_codes = generate_backup_codes_command()
    encrypted_backup_codes = ",".join([make_password(_) for _ in backup_codes])
    if created:
        user.set_password("secretkey"),
        user.is_active = True
        user.save()
        mfa_method_creator(user=user, method_name="email", _backup_codes=encrypted_backup_codes)
        mfa_method_creator(user=user, method_name="sms_twilio", is_primary=False, _backup_codes=encrypted_backup_codes)
        mfa_method_creator(user=user, method_name="app", is_primary=False, _backup_codes=encrypted_backup_codes)
        mfa_method_creator(user=user, method_name="yubi", is_primary=False, _backup_codes=encrypted_backup_codes)
    return user, next(iter(backup_codes))


@pytest.fixture()
def active_user():
    user, created = User.objects.get_or_create(
        username="hetephernebti",
        email="hetephernebti@pyramids.eg",
    )
    if created:
        user.set_password("secretkey"),
        user.is_active = True
        user.save()

    return user


@pytest.fixture()
def inactive_user():
    user, created = User.objects.get_or_create(
        username="ramzes",
        email="ramzes@pyramids.eg",
    )
    if created:
        user.set_password("secretkey"),
        user.is_active = False
        user.save()

    return user


@pytest.fixture()
def admin_user():
    return User.objects.create_superuser(
        username="admin",
        email="admin@admin.com",
        is_active=True,
        password="secretkey",
    )


FAKE_YUBI_SECRET = "testtesttesttesttesttesttesttest"


@pytest.fixture()
def active_user_with_yubi():
    user, created = User.objects.get_or_create(
        username="ramses",
        email="ramses@thegreat.eg",
    )
    backup_codes = generate_backup_codes_command()
    encrypted_backup_codes = ",".join([make_password(_) for _ in backup_codes])
    if created:
        user.set_password("secretkey"),
        user.is_active = True
        user.save()
        mfa_method_creator(user=user, method_name="yubi", secret=FAKE_YUBI_SECRET, _backup_codes=encrypted_backup_codes)
    return user


@pytest.fixture()
def fake_yubikey(monkeypatch):
    def mock_getattribute(self, name):
        if name == "device_id":
            return FAKE_YUBI_SECRET
        return super(OTP, self).__getattribute__(name)

    monkeypatch.setattr(target=OTP, name="__getattribute__", value=mock_getattribute)


@pytest.fixture()
def offline_yubikey(monkeypatch, fake_yubikey):
    def mock_verify(*args, **kwargs):
        return True

    monkeypatch.setattr(target=Yubico, name="verify", value=mock_verify)
    assert OTP("123456").device_id == FAKE_YUBI_SECRET



