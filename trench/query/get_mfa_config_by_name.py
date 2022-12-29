from typing import Any, Dict

from trench.exceptions import MFAMethodDoesNotExistError
from trench.settings import trench_settings

from trench.domain.models import TrenchConfig

class GetMFAConfigByNameQuery:
    def __init__(self, settings: TrenchConfig) -> None:
        self._settings = settings

    def execute(self, name: str) -> Dict[str, Any]:
        try:
            return self._settings.mfa_methods[name]
        except KeyError as cause:
            raise MFAMethodDoesNotExistError from cause


get_mfa_config_by_name_query = GetMFAConfigByNameQuery(settings=trench_settings).execute
