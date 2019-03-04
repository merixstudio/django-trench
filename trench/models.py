from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class MFAMethod(models.Model):
    """
    Base model with MFA information linked to user.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('user'),
        related_name='mfa_methods',
    )
    name = models.CharField(
        _('name'),
        max_length=255,
    )
    secret = models.CharField(
        _('secret'),
        max_length=255,
    )
    is_primary = models.BooleanField(
        _('is primary'),
        default=False,
    )
    is_active = models.BooleanField(
        _('is active'),
        default=False,
    )
    _backup_codes = models.TextField(
        _('backup codes'),
        blank=True,
    )

    class Meta:
        verbose_name = _('MFA Method')
        verbose_name_plural = _('MFA Methods')

    def __str__(self):
        return '{} (User id: {})'.format(self.name, self.user_id)

    @property
    def backup_codes(self):
        return self._backup_codes.split(',')

    @backup_codes.setter
    def backup_codes(self, codes):
        self._backup_codes = ','.join(codes)

    def remove_backup_code(self, utilised_code):
        codes = self.backup_codes
        if utilised_code in codes:
            codes.remove(utilised_code)
            self.backup_codes = codes
            self.save()
