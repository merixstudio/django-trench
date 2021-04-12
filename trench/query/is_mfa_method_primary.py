from typing_extensions import Type

from trench.models import MFAMethod
from trench.utils import get_mfa_model


class IsMFAMethodPrimary:
    def __init__(self, mfa_model: Type[MFAMethod]):
        self._mfa_model = mfa_model

    def execute(self, user_id: int, name: str) -> bool:
        return (
            self._mfa_model.objects.filter(user_id=user_id, name=name)
            .values_list("is_primary", flat=True)
            .first()
        )


is_mfa_method_primary = IsMFAMethodPrimary(mfa_model=get_mfa_model()).execute
