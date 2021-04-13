from typing_extensions import Type

from trench.exceptions import MFAMethodDoesNotExistError
from trench.models import MFAMethod
from trench.utils import get_mfa_model


class GetPrimaryActiveMFAMethodQuery:
    def __init__(self, mfa_model: Type[MFAMethod]):
        self._mfa_model = mfa_model

    def execute(self, user_id: int) -> MFAMethod:
        mfa_method = self._mfa_model.objects.filter(
            user_id=user_id, is_primary=True, is_active=True
        ).first()
        if mfa_method is None:
            raise MFAMethodDoesNotExistError()
        return mfa_method


get_primary_active_mfa_method_query = GetPrimaryActiveMFAMethodQuery(
    mfa_model=get_mfa_model()
).execute
