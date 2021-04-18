from typing import Type

from trench.models import MFAMethod
from trench.utils import get_mfa_model


class GetActiveMFAMethodsCount:
    def __init__(self, mfa_model: Type[MFAMethod]):
        self._mfa_model = mfa_model

    def execute(self, user_id: int) -> int:
        return self._mfa_model.objects.filter(user_id=user_id, is_active=True).count()


get_active_mfa_methods_count = GetActiveMFAMethodsCount(
    mfa_model=get_mfa_model()
).execute
