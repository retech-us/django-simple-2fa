import typing

from django.utils.translation import gettext_lazy as _

from .throttling import ThrottleStatus


__all__ = (
    'TwoFactorAuthError',
)


class TwoFactorAuthError(Exception):
    throttle_status: typing.Optional[ThrottleStatus] = None
    reason: str

    def __init__(self,
                 reason: typing.Optional[str] = None, *,
                 throttle_status: typing.Optional[ThrottleStatus] = None) -> None:
        self.throttle_status = throttle_status
        self.reason = reason

        if throttle_status and not throttle_status.is_allowed and not self.reason:
            self.reason = _(
                'We\'ve locked you because of too many login attempts. '
                'Try again in {waiting_time}.'
            ).format(
                waiting_time=throttle_status.str_waiting_time,
            )

    def __str__(self) -> str:
        return self.reason
