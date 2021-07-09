import datetime
import time
import typing
from dataclasses import dataclass

from django.core.cache import cache

from .settings import app_settings


@dataclass
class RateThrottleCondition:
    max_attempts: int
    duration: datetime.timedelta


@dataclass
class ThrottleStatus:
    history: typing.List[float]
    condition: RateThrottleCondition
    is_allowed: bool
    timestamp: float

    @property
    def num_attempts(self) -> int:
        return len(self.history)

    @property
    def locking_time(self) -> int:
        diff = int(self.timestamp - self.history[-1])

        if diff >= self.condition.duration.total_seconds():
            return 0

        return int(self.condition.duration.total_seconds() - diff)

    @property
    def waiting_time(self) -> int:
        if not self.is_spent_all_attempts:
            return 0

        return self.locking_time

    @property
    def str_locking_time(self) -> str:
        from .utils import convert_seconds_to_str
        return convert_seconds_to_str(self.locking_time, round_time=True)

    @property
    def str_waiting_time(self) -> str:
        from .utils import convert_seconds_to_str
        return convert_seconds_to_str(self.waiting_time, round_time=True)

    @property
    def is_spent_all_attempts(self) -> bool:
        return not self.remaining_attempts

    @property
    def remaining_attempts(self) -> int:
        if self.num_attempts > self.condition.max_attempts:
            return 0

        return self.condition.max_attempts - self.num_attempts


class RateThrottle:
    cache = cache
    timer = time.time
    cache_format = 'rate-throttle:{ident}:{scope}'
    scope: str
    condition: RateThrottleCondition

    def __init__(self, *, scope: str, condition: RateThrottleCondition) -> None:
        self.scope = scope
        self.condition = condition

    def check(self, ident: str, increase_attempts: bool = True) -> ThrottleStatus:
        history = self._get_history(ident)
        now = time.time()

        if len(history) >= self.condition.max_attempts:
            return ThrottleStatus(history=history, is_allowed=False, condition=self.condition, timestamp=now)

        if increase_attempts:
            history.append(now)

        self._save_history(history, ident=ident)

        return ThrottleStatus(history=history, is_allowed=True, condition=self.condition, timestamp=now)

    def increase_attempts(self, ident: str) -> ThrottleStatus:
        now = time.time()

        history = self._get_history(ident)
        history.append(now)
        self._save_history(history, ident=ident)

        return ThrottleStatus(
            history=history,
            is_allowed=len(history) <= self.condition.max_attempts,
            condition=self.condition,
            timestamp=now,
        )

    def reset(self, ident: str) -> None:
        cache_key = self._get_cache_key(ident)
        self.cache.delete(cache_key)

    def _save_history(self, history: typing.List[float], *, ident: str) -> None:
        if not app_settings.THROTTLING_IS_ENABLED():
            return

        cache_key = self._get_cache_key(ident)
        self.cache.set(cache_key, history, self.condition.duration.total_seconds())

    def _get_history(self, ident: str) -> typing.List[float]:
        cache_key = self._get_cache_key(ident)
        history = cache.get(cache_key, [])

        now = time.time()

        while history and now - history[-1] >= self.condition.duration.total_seconds():
            history.pop()

        return history

    def _get_cache_key(self, ident: str) -> str:
        return self.cache_format.format(ident=ident, scope=self.scope)


rate_throttle_for_auth = RateThrottle(
    scope='2fa-auth',
    condition=RateThrottleCondition(max_attempts=3, duration=datetime.timedelta(minutes=5)),
)

rate_throttle_for_obtain = RateThrottle(
    scope='2fa-obtain',
    condition=RateThrottleCondition(max_attempts=3, duration=datetime.timedelta(minutes=5)),
)

rate_throttle_for_verify = RateThrottle(
    scope='2fa-verify',
    condition=RateThrottleCondition(max_attempts=3, duration=datetime.timedelta(minutes=5)),
)
