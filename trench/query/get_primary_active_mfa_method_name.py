from typing_extensions import Type

from trench.exceptions import MFAMethodDoesNotExistError
from trench.models import MFAMethod
from trench.utils import get_mfa_model


class GetPrimaryActiveMFAMethodNameQuery:
    def __init__(self, mfa_model: Type[MFAMethod]):
        self._mfa_model = mfa_model

    def execute(self, user_id: int) -> str:
        mfa_method_name = (
            self._mfa_model.objects.filter(
                user_id=user_id, is_primary=True, is_active=True
            )
            .values_list("name", flat=True)
            .first()
        )
        if mfa_method_name is None:
            raise MFAMethodDoesNotExistError()
        return mfa_method_name


get_primary_active_mfa_method_name_query = GetPrimaryActiveMFAMethodNameQuery(
    mfa_model=get_mfa_model()
).execute
