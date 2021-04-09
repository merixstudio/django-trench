from trench.models import MFAMethod
from trench.utils import get_mfa_model, create_secret


class UpsertMFAMethodCommand:
    def __init__(self, secret_generator, mfa_model):
        self._mfa_model = mfa_model
        self._create_secret = secret_generator

    def execute(self, user_id: int, name: str, is_active: bool) -> MFAMethod:
        return MFAMethod.objects.get_or_create(
            user_id=user_id,
            name=name,
            defaults={
                "secret": self._create_secret,
                "is_active": is_active,
            },
        )


upsert_mfa_method_command = UpsertMFAMethodCommand(
    secret_generator=create_secret, mfa_model=get_mfa_model()
).execute
