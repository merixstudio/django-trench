import pytest

from trench.exceptions import MFAMethodDoesNotExistError
from trench.query.get_mfa_config_by_name import get_mfa_config_by_name_query


@pytest.mark.django_db(transaction=True)
def test_get_non_existing_mfa_method_by_name():
    with pytest.raises(MFAMethodDoesNotExistError):
        get_mfa_config_by_name_query(name="not_existing")
