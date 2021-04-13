from trench.exceptions import MFAMethodDoesNotExistError
from trench.models import MFAMethod
from trench.utils import get_mfa_model


class GetMFAMethodQuery:
    def __init__(self, mfa_model: MFAMethod):
        self._mfa_model = mfa_model

    def execute(self, user_id: int, name: str) -> MFAMethod:
        mfa = self._mfa_model.objects.filter(user_id=user_id, name=name).first()
        if mfa is None:
            raise MFAMethodDoesNotExistError
        return mfa


get_mfa_method_query = GetMFAMethodQuery(mfa_model=get_mfa_model()).execute
