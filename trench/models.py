from django.conf import settings
from django.db.models import (
    CASCADE,
    BooleanField,
    Case,
    CharField,
    Exists,
    F,
    ForeignKey,
    Manager,
    Model,
    OuterRef,
    QuerySet,
    TextField,
    When,
)
from django.utils.translation import gettext_lazy as _

from typing import Any, Iterable

from trench.exceptions import MFAMethodDoesNotExistError


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

    def annotate_is_primary_mfa_method(self):
        primary_method_for_user_queryset = self.model.objects.filter(user_id=OuterRef('user_id'), is_primary=True)
        return self.annotate(
            is_primary_mfa_method=Case(When(name=F('name'), is_primary=True, then=True),
                                       When(~Exists(primary_method_for_user_queryset), then=True),
                                       default=False,
                                       output_field=BooleanField()),
        )


class MFAMethod(Model):
    _BACKUP_CODES_DELIMITER = "|"

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
    _backup_codes = TextField(_("backup codes"), blank=True)

    class Meta:
        verbose_name = _("MFA Method")
        verbose_name_plural = _("MFA Methods")

    objects = MFAUserMethodManager()

    def __str__(self) -> str:
        return f"{self.name} (User id: {self.user_id})"

    @property
    def backup_codes(self) -> Iterable[str]:
        return self._backup_codes.split(self._BACKUP_CODES_DELIMITER)

    @backup_codes.setter
    def backup_codes(self, codes: Iterable) -> None:
        self._backup_codes = self._BACKUP_CODES_DELIMITER.join(codes)
