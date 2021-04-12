from django.db.models import QuerySet

from typing_extensions import Type

from trench.models import MFAMethod
from trench.utils import get_mfa_model


class ListActiveMFAMethodsQuery:
    def __init__(self, mfa_model: Type[MFAMethod]):
        self._mfa_model = mfa_model

    def execute(self, user_id: int) -> QuerySet:
        return self._mfa_model.objects.filter(user_id=user_id, is_active=True)


list_active_mfa_methods_query = ListActiveMFAMethodsQuery(
    mfa_model=get_mfa_model()
).execute
