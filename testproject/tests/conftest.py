import pytest

from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from trench.command.create_secret import create_secret_command
from trench.command.generate_backup_codes import generate_backup_codes_command

User = get_user_model()


@pytest.fixture()
def active_user_with_email_otp():
    user, created = User.objects.get_or_create(
        username='imhotep',
        email='imhotep@pyramids.eg',
    )
    if created:
        user.set_password('secretkey'),
        user.is_active = True
        user.save()

        MFAMethod = apps.get_model('trench.MFAMethod')
        MFAMethod.objects.create(
            user=user,
            secret=create_secret_command(),
            is_primary=True,
            name='email',
            is_active=True,
        )

    return user


@pytest.fixture()
def active_user_with_sms_otp():
    user, created = User.objects.get_or_create(
        username='imhotep',
        email='imhotep@pyramids.eg',
        phone_number='555-555-555'
    )
    if created:
        user.set_password('secretkey'),
        user.is_active = True
        user.save()

        MFAMethod = apps.get_model('trench.MFAMethod')
        MFAMethod.objects.create(
            user=user,
            secret=create_secret_command(),
            is_primary=True,
            name='sms_twilio',
            is_active=True,
        )

    return user


@pytest.fixture()
def active_user_with_email_and_inactive_other_methods_otp():
    user, created = User.objects.get_or_create(
        username='imhotep',
        email='imhotep@pyramids.eg',
    )
    if created:
        user.set_password('secretkey'),
        user.is_active = True
        user.save()

        MFAMethod = apps.get_model('trench.MFAMethod')
        MFAMethod.objects.create(
            user=user,
            secret=create_secret_command(),
            is_primary=True,
            name='email',
            is_active=True,
        )
        MFAMethod.objects.create(
            user=user,
            secret=create_secret_command(),
            is_primary=False,
            name='sms_twilio',
            is_active=False,
        )
        MFAMethod.objects.create(
            user=user,
            secret=create_secret_command(),
            is_primary=False,
            name='app',
            is_active=False,
        )

    return user


@pytest.fixture()
def active_user_with_backup_codes():
    user, created = User.objects.get_or_create(
        username='cleopatra',
        email='cleopatra@pyramids.eg',
    )
    backup_codes = generate_backup_codes_command()
    encrypted_backup_codes = ','.join([make_password(_) for _ in backup_codes])
    if created:
        user.set_password('secretkey'),
        user.is_active = True
        user.save()

        MFAMethod = apps.get_model('trench.MFAMethod')
        MFAMethod.objects.create(
            user=user,
            secret=create_secret_command(),
            is_primary=True,
            name='email',
            is_active=True,
            _backup_codes=encrypted_backup_codes,
        )

    return user, next(iter(backup_codes))


@pytest.fixture()
def active_user_with_many_otp_methods():
    user, created = User.objects.get_or_create(
        username='ramses',
        email='ramses@thegreat.eg',
    )
    backup_codes = generate_backup_codes_command()
    encrypted_backup_codes = ','.join([make_password(_) for _ in backup_codes])
    if created:
        user.set_password('secretkey'),
        user.is_active = True
        user.save()

        MFAMethod = apps.get_model('trench.MFAMethod')
        MFAMethod.objects.create(
            user=user,
            secret=create_secret_command(),
            is_primary=True,
            name='email',
            is_active=True,
            _backup_codes=encrypted_backup_codes,
        )
        MFAMethod.objects.create(
            user=user,
            secret=create_secret_command(),
            is_primary=False,
            name='sms_twilio',
            is_active=True,
            _backup_codes=encrypted_backup_codes,
        )
        MFAMethod.objects.create(
            user=user,
            secret=create_secret_command(),
            is_primary=False,
            name='app',
            is_active=True,
            _backup_codes=encrypted_backup_codes,
        )
        MFAMethod.objects.create(
            user=user,
            is_primary=False,
            name='yubi',
            is_active=True,
            _backup_codes=encrypted_backup_codes,
        )

    return user, next(iter(backup_codes))


@pytest.fixture()
def active_user():
    user, created = User.objects.get_or_create(
        username='hetephernebti',
        email='hetephernebti@pyramids.eg',
    )
    if created:
        user.set_password('secretkey'),
        user.is_active = True
        user.save()

    return user


@pytest.fixture()
def inactive_user():
    user, created = User.objects.get_or_create(
        username='ramzes',
        email='ramzes@pyramids.eg',
    )
    if created:
        user.set_password('secretkey'),
        user.is_active = False
        user.save()

    return user


@pytest.fixture()
def admin_user():
    return User.objects.create_superuser(
        username='admin',
        email='admin@admin.com',
        is_active=True,
        password='secretkey',
    )
