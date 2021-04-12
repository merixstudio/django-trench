from typing_extensions import Type

from trench.models import MFAMethod
from trench.utils import get_mfa_model


class PrimaryMFAMethodExistsQuery:
    def __init__(self, mfa_model: Type[MFAMethod]):
        self._mfa_model = mfa_model

    def execute(self, user_id: int) -> bool:
        return self._mfa_model.objects.filter(user_id=user_id, is_active=True).exists()


primary_mfa_method_exists_query = PrimaryMFAMethodExistsQuery(
    mfa_model=get_mfa_model()
).execute
