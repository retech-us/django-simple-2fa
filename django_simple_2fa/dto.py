import typing
from dataclasses import dataclass
from django.contrib.auth import authenticate, get_user_model
from django.utils.functional import cached_property

from .throttling import ThrottleStatus


if typing.TYPE_CHECKING:
    from .auth_types.base import BaseTwoFactorAuthType

__all__ = (
    'TwoFactorAuthObtainResult',
    'TwoFactorAuthVerifyResult',
    'TwoFactorAuthStatus',
    'TwoFactorRequester',
)

UserModel = get_user_model()


@dataclass
class TwoFactorAuthObtainResult:
    message: str
    verification_code: str
    throttle_status: typing.Optional[ThrottleStatus] = None


@dataclass
class TwoFactorAuthStatus:
    two_factor_type: typing.Type['BaseTwoFactorAuthType']
    throttle_status: ThrottleStatus


@dataclass
class TwoFactorAuthVerifyResult:
    user: UserModel
    throttle_status: ThrottleStatus


@dataclass
class TwoFactorRequester:
    username: str
    password: str
    ip: str
    device_id: typing.Optional[str] = None

    @cached_property
    def user(self) -> typing.Optional[UserModel]:
        return authenticate(username=self.username, password=self.password)

    @cached_property
    def two_factor_auth_type(self) -> typing.Optional[typing.Type['BaseTwoFactorAuthType']]:
        from . import utils

        if not self.user or not self.user.is_active:
            return None

        return utils.get_two_factor_auth_type(user=self.user, device_id=self.device_id)
