from django.conf import settings
from django.db.models import (
    CASCADE,
    BooleanField,
    CharField,
    ForeignKey,
    Model,
    TextField,
)
from django.utils.translation import gettext_lazy as _

from typing import Iterable, List


class MFAMethod(Model):
    """
    Base model with MFA information linked to user.
    """

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

    def __str__(self) -> str:
        return f"{self.name} (User id: {self.user_id})"

    @property
    def backup_codes(self) -> List[str]:
        return self._backup_codes.split(",")

    @backup_codes.setter
    def backup_codes(self, codes: Iterable):
        self._backup_codes = ",".join(codes)

    def remove_backup_code(self, utilised_code: str):
        codes = self.backup_codes
        if utilised_code in codes:
            codes.remove(utilised_code)
            self.backup_codes = codes
            self.save()
