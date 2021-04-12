from typing import Callable

from trench.exceptions import MFAMethodAlreadyActiveError
from trench.models import MFAMethod
from trench.utils import create_secret, get_mfa_model


class CreateMFAMethodCommand:
    def __init__(self, secret_generator: Callable, mfa_model: MFAMethod):
        self._mfa_model = mfa_model
        self._create_secret = secret_generator

    def execute(self, user_id: int, name: str) -> MFAMethod:
        mfa, created = self._mfa_model.objects.get_or_create(
            user_id=user_id,
            name=name,
            defaults={
                "secret": self._create_secret,
                "is_active": False,
            },
        )
        if not created and mfa.is_active:
            raise MFAMethodAlreadyActiveError()
        return mfa


create_mfa_method_command = CreateMFAMethodCommand(
    secret_generator=create_secret, mfa_model=get_mfa_model()
).execute
