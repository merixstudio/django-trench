from django.conf import settings
from django.db.models import (
    CASCADE,
    IntegerField,
    BooleanField,
    CharField,
    CheckConstraint,
    ForeignKey,
    Manager,
    Model,
    Q,
    QuerySet,
    TextField,
    UniqueConstraint,
    DateTimeField
)
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import datetime
from typing import Any, Iterable

from trench.exceptions import MFAMethodDoesNotExistError
import uuid

class MFAUserMethodManager(Manager):
    def get_by_name(self, user_id: Any, name: str) -> "MFAMethod":
        try:
            return self.get(user_id=user_id, name=name)
        except self.model.DoesNotExist:
            raise MFAMethodDoesNotExistError()

    def get_primary_active(self, user_id: Any) -> "MFAMethod":
        try:
            return self.get(user_id=user_id, is_primary=True, is_active=True)
        except self.model.DoesNotExist:
            raise MFAMethodDoesNotExistError()

    def get_primary_active_name(self, user_id: Any) -> str:
        method_name = (
            self.filter(user_id=user_id, is_primary=True, is_active=True)
            .values_list("name", flat=True)
            .first()
        )
        if method_name is None:
            raise MFAMethodDoesNotExistError()
        return method_name

    def is_active_by_name(self, user_id: Any, name: str) -> bool:
        is_active = (
            self.filter(user_id=user_id, name=name)
            .values_list("is_active", flat=True)
            .first()
        )
        if is_active is None:
            raise MFAMethodDoesNotExistError()
        return is_active

    def list_active(self, user_id: Any) -> QuerySet:
        return self.filter(user_id=user_id, is_active=True)

    def primary_exists(self, user_id: Any) -> bool:
        return self.filter(user_id=user_id, is_primary=True).exists()


class MFAUsedCode(Model):
    id = CharField(_("id"), max_length=255, default=uuid.uuid4, primary_key=True)
    user = ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=CASCADE,
        verbose_name=_("user"),
        related_name="mfa_used_codes",
    )
    code = CharField(_("code"), max_length=6)
    used_at = DateTimeField(_("used_at"), auto_now_add=True)
    expires_at = DateTimeField(_("expires_at"))
    method = CharField(_("method"), max_length=255)

    class Meta:
        verbose_name = _("MFA Last Used Code")
        verbose_name_plural = _("MFA Last Used Codes")

    def __str__(self) -> str:
        return f"{self.id} (User id: {self.user_id})"


class MFABackupCodes(Model):
    _BACKUP_CODES_DELIMITER = "|"
    user = ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=CASCADE,
        verbose_name=_("user"),
        related_name="mfa_backup_codes",
        primary_key=True
    )
    _values = TextField(_("backup codes"))

    class Meta:
        verbose_name = _("MFA Backup Code")
        verbose_name_plural = _("MFA Backup Codes")

    @property
    def values(self) -> Iterable[str]:
        return self._values.split(self._BACKUP_CODES_DELIMITER)

    @values.setter
    def values(self, codes: Iterable) -> None:
        self._values = self._BACKUP_CODES_DELIMITER.join(codes)


class MFAMethod(Model):
    user = ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=CASCADE,
        verbose_name=_("user"),
        related_name="mfa_methods",
    )
    name = CharField(_("name"), max_length=255)
    secret = CharField(_("secret"), max_length=255)
    is_primary = BooleanField(_("is primary"), default=False)
    is_active = BooleanField(_("is active"), default=False)

    class Meta:
        verbose_name = _("MFA Method")
        verbose_name_plural = _("MFA Methods")
        constraints = (
            UniqueConstraint(
                condition=Q(is_primary=True),
                fields=("user",),
                name="unique_user_is_primary",
            ),
            CheckConstraint(
                check=(Q(is_primary=True) & Q(is_active=True)) | Q(is_primary=False),
                name="primary_is_active",
            ),
        )

    objects = MFAUserMethodManager()

    def __str__(self) -> str:
        return f"{self.name} (User id: {self.user_id})"
