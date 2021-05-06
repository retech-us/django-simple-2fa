import typing

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from . import utils
from .auth_types import DirectTwoFactorAuthType
from .dto import TwoFactorAuthObtainResult, TwoFactorAuthStatus, TwoFactorAuthVerifyResult, TwoFactorRequester
from .errors import TwoFactorAuthError
from .settings import app_settings
from .throttling import RateThrottle, ThrottleStatus


__all__ = (
    'TwoFactorAuth',
)

UserModel = get_user_model()


class TwoFactorAuth:
    requester: TwoFactorRequester
    _requester_ident: str
    _rate_throttle_for_auth: RateThrottle
    _rate_throttle_for_obtain: RateThrottle
    _rate_throttle_for_verify: RateThrottle
    _user_auth_security: utils.UserAuthSecurity

    def __init__(self, requester: TwoFactorRequester) -> None:
        self.requester = requester
        self._user_auth_security = app_settings.USER_AUTH_SECURITY_CLASS(self.requester.username)
        self._requester_ident = f'{requester.username}-{requester.ip}'
        self._rate_throttle_for_auth = app_settings.RATE_THROTTLE_FOR_AUTH
        self._rate_throttle_for_obtain = app_settings.RATE_THROTTLE_FOR_OBTAIN
        self._rate_throttle_for_verify = app_settings.RATE_THROTTLE_FOR_VERIFY

    def get_status(self) -> TwoFactorAuthStatus:
        throttle_status = self._check_throttle_for_auth()

        return TwoFactorAuthStatus(
            two_factor_type=self.requester.two_factor_auth_type,
            throttle_status=throttle_status,
        )

    def obtain(self) -> TwoFactorAuthObtainResult:
        self._check_throttle_for_auth()

        throttle_status = self._rate_throttle_for_obtain.check(self._requester_ident)

        if not throttle_status.is_allowed:
            raise TwoFactorAuthError(
                _('You have made a lot of requests. Try again in {waiting_time}.').format(
                    waiting_time=throttle_status.str_waiting_time,
                ),
                throttle_status=throttle_status,
            )

        try:
            result = self.requester.two_factor_auth_type.obtain(user=self.requester.user)
        except TwoFactorAuthError as e:
            e.throttle_status = throttle_status
            raise
        else:
            result.throttle_status = throttle_status

        # Reset attempts for `verify()`.
        self._rate_throttle_for_verify.reset(self._requester_ident)

        return result

    def verify(self, verification_code: typing.Optional[str] = None) -> TwoFactorAuthVerifyResult:
        self._check_throttle_for_auth()

        throttle_status = self._rate_throttle_for_verify.check(self._requester_ident, increase_attempts=False)
        auth_type = self.requester.two_factor_auth_type

        if not throttle_status.is_allowed:
            if issubclass(auth_type, DirectTwoFactorAuthType):
                reason = None
            else:
                auth_type.reset(user=self.requester.user)
                reason = _('After many failed attempts we removed your code. You need to request a code again.')

            raise TwoFactorAuthError(throttle_status=throttle_status, reason=reason)

        code_is_valid = auth_type.is_valid(user=self.requester.user, verification_code=verification_code)

        if not code_is_valid:
            self._user_auth_security.add_failed_login_attempt(self.requester.ip)
            throttle_status = self._rate_throttle_for_verify.increase_attempts(self._requester_ident)

            raise TwoFactorAuthError(
                _('Invalid verification code.'),
                throttle_status=throttle_status,
            )

        # Save user device
        user_device_manager = utils.UserDeviceManager(self.requester.user)
        user_device_manager.add_device(self.requester.device_id)

        return TwoFactorAuthVerifyResult(
            user=self.requester.user,
            throttle_status=throttle_status,
        )

    def _check_throttle_for_auth(self) -> ThrottleStatus:
        throttle_status = self._rate_throttle_for_auth.check(self._requester_ident, increase_attempts=False)

        if not throttle_status.is_allowed:
            raise TwoFactorAuthError(throttle_status=throttle_status)

        if not self.requester.user or not self.requester.user.is_active:
            if not self.requester.user:
                # Increase attempts only for failed login.
                self._user_auth_security.add_failed_login_attempt(self.requester.ip)
                throttle_status = self._rate_throttle_for_auth.increase_attempts(self._requester_ident)

            raise TwoFactorAuthError(
                _('No active account found with the given credentials.'),
                throttle_status=throttle_status,
            )

        return throttle_status
