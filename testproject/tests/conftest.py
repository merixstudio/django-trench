import pytest

from django.apps import apps
from django.contrib.auth import get_user_model

from trench.utils import create_secret, generate_backup_codes


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
            secret=create_secret(),
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
            secret=create_secret(),
            is_primary=True,
            name='sms',
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
            secret=create_secret(),
            is_primary=True,
            name='email',
            is_active=True,
        )
        MFAMethod.objects.create(
            user=user,
            secret=create_secret(),
            is_primary=False,
            name='sms',
            is_active=False,
        )
        MFAMethod.objects.create(
            user=user,
            secret=create_secret(),
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
    if created:
        user.set_password('secretkey'),
        user.is_active = True
        user.save()

        MFAMethod = apps.get_model('trench.MFAMethod')
        MFAMethod.objects.create(
            user=user,
            secret=create_secret(),
            is_primary=True,
            name='email',
            is_active=True,
            backup_codes=generate_backup_codes(),
        )

    return user


@pytest.fixture()
def active_user_with_many_otp_methods():
    user, created = User.objects.get_or_create(
        username='ramses',
        email='ramses@thegreat.eg',
    )
    if created:
        user.set_password('secretkey'),
        user.is_active = True
        user.save()

        MFAMethod = apps.get_model('trench.MFAMethod')
        MFAMethod.objects.create(
            user=user,
            secret=create_secret(),
            is_primary=True,
            name='email',
            is_active=True,
            backup_codes=generate_backup_codes(),
        )
        MFAMethod.objects.create(
            user=user,
            secret=create_secret(),
            is_primary=False,
            name='sms',
            is_active=True,
            backup_codes=generate_backup_codes(),
        )
        MFAMethod.objects.create(
            user=user,
            secret=create_secret(),
            is_primary=False,
            name='app',
            is_active=True,
            backup_codes=generate_backup_codes(),
        )
        MFAMethod.objects.create(
            user=user,
            is_primary=False,
            name='yubi',
            is_active=True,
            backup_codes=generate_backup_codes(),
        )

    return user


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
        username='djoser',
        email='djoser@pyramids.eg',
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
