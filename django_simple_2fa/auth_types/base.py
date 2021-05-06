from django.contrib.auth import get_user_model

from ..dto import TwoFactorAuthObtainResult


__all__ = (
    'BaseTwoFactorAuthType',
)

UserModel = get_user_model()


class BaseTwoFactorAuthType:
    name: str
    type: str

    @classmethod
    def obtain(cls, *, user: UserModel) -> TwoFactorAuthObtainResult:
        pass

    @classmethod
    def reset(cls, *, user: UserModel) -> None:
        pass

    @classmethod
    def is_valid(cls, *,
                 user: UserModel,
                 verification_code: str) -> bool:
        pass
