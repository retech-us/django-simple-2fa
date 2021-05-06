from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .base import BaseTwoFactorAuthType
from ..dto import TwoFactorAuthObtainResult


__all__ = (
    'DirectTwoFactorAuthType',
)

UserModel = get_user_model()


class DirectTwoFactorAuthType(BaseTwoFactorAuthType):
    name = 'Direct (without 2FA)'
    type = 'direct'

    @classmethod
    def obtain(cls, *, user: UserModel) -> TwoFactorAuthObtainResult:
        return TwoFactorAuthObtainResult(
            message=_('You do not need to use 2FA.'),
            verification_code='',
        )

    @classmethod
    def reset(cls, *, user: UserModel) -> None:
        pass

    @classmethod
    def is_valid(cls, *,
                 user: UserModel,
                 verification_code: str) -> bool:
        return True
