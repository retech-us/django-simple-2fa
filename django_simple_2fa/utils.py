import datetime
import logging
import time
import typing

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import HttpRequest
from django.template import loader
from rest_framework.settings import api_settings

from .auth_types.base import BaseTwoFactorAuthType
from .auth_types.direct import DirectTwoFactorAuthType
from .settings import app_settings
from .throttling import RateThrottle, RateThrottleCondition


UserModel = get_user_model()


def get_ip_from_request(request: HttpRequest) -> str:
    """
    Identify the machine making the request by parsing HTTP_X_FORWARDED_FOR
    if present and number of proxies is > 0. If not use all of
    HTTP_X_FORWARDED_FOR if it is available, if not use REMOTE_ADDR.

    Сopied from rest_framework.throttling.BaseThrottle.get_ident.
    """
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    remote_addr = request.META.get('REMOTE_ADDR')

    if not xff and not remote_addr:
        logging.error('HTTP_X_FORWARDED_FOR and REMOTE_ADDR are empty.')

    num_proxies = api_settings.NUM_PROXIES

    if num_proxies is not None:
        if num_proxies == 0 or xff is None:
            return remote_addr

        addrs = xff.split(',')
        client_addr = addrs[-min(num_proxies, len(addrs))]
        return client_addr.strip()

    return ''.join(xff.split()) if xff else remote_addr


class UserAuthSecurity:
    username: str
    user: UserModel
    _rate_throttle: RateThrottle

    # _failed_attempts_to_reset_password: int = 1_000

    def __init__(self, username: str) -> None:
        self.username = username
        self.user = UserModel.objects.filter(username=self.username).first()
        self._rate_throttle = RateThrottle(
            scope='user-auth-security',
            condition=RateThrottleCondition(max_attempts=10, duration=datetime.timedelta(hours=2)),
        )

    def add_failed_login_attempt(self, ip: str) -> None:
        if not self.user:
            return

        # cache_key = f'failed-login-attempts:{self.username}'
        # failed_attempts = cache.get(cache_key, 0)
        # failed_attempts += 1
        #
        # if failed_attempts > self._failed_attempts_to_reset_password:
        #     cache.clear(cache_key)
        #     # TODO: Need to discuss this logic
        #     # self._reset_password()
        # else:
        #     cache.set(cache_key, failed_attempts, datetime.timedelta(weeks=1).total_seconds())

        status = self._rate_throttle.increase_attempts(self.username)

        if status.is_spent_all_attempts:
            self._rate_throttle.reset(self.user)
            self.react_on_failed_attempts(ip=ip)

    def react_on_failed_attempts(self, *, ip: str) -> None:
        cache_key = f'notification-about-login-attempts:{self.user.id}'
        need_to_notify = cache.get(cache_key) is None

        if need_to_notify:
            context = self.get_context_for_letter(ip=ip)
            self.send_notification_about_login_attempts(context)
            cache.set(cache_key, time.time(), datetime.timedelta(minutes=30).total_seconds())

    def send_notification_about_login_attempts(self, context: dict) -> None:
        if not self.user.email:
            return

        message = loader.render_to_string(
            'two_factor_auth_letters/many_attempts.txt',
            context=context,
        )

        send_mail(
            subject='Too many failed login attempts',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.user.email],
        )

    def get_context_for_letter(self, *, ip: str) -> dict:
        return {
            'ip': ip,
            'user': self.user,
        }

    # def _reset_password(self) -> None:
    #     from ....services.password_changer import PasswordChanger
    #
    #     if not self.user:
    #         return
    #
    #     password_changer = PasswordChanger()
    #     password_changer.set_unusable_password(self.user)
    #     password_changer.reset_password(self.user)


class UserDeviceManager:
    user: UserModel
    _device_ttl = datetime.timedelta(weeks=4)
    _cache_key_tpl = 'used-device:{user_id}:{device_id}'

    def __init__(self, user: UserModel) -> None:
        self.user = user

    def add_device(self, device_id: str) -> None:
        cache_key = self._cache_key_tpl.format(user_id=self.user.id, device_id=device_id)
        cache.set(cache_key, time.time(), self._device_ttl.total_seconds())

    def has_device(self, device_id: str) -> bool:
        cache_key = self._cache_key_tpl.format(user_id=self.user.id, device_id=device_id)
        return cache.get(cache_key) is not None


def get_two_factor_auth_type(*,
                             user: UserModel,
                             device_id: typing.Optional[str] = None) -> typing.Type[BaseTwoFactorAuthType]:
    user_device_manager = UserDeviceManager(user)

    if not app_settings.IS_ENABLED() or (device_id and user_device_manager.has_device(device_id)):
        return DirectTwoFactorAuthType

    if app_settings.USER_TWO_FACTOR_TYPE_GETTER:
        return app_settings.USER_TWO_FACTOR_TYPE_GETTER(user=user)

    return app_settings.DEFAULT_TWO_FACTOR_TYPE


def convert_seconds_to_str(seconds: int, *, only_first: bool = False, round_time: bool = False) -> str:
    periods = (
        ('year', 60 * 60 * 24 * 365,),
        ('month', 60 * 60 * 24 * 30,),
        ('day', 60 * 60 * 24,),
        ('hour', 60 * 60,),
        ('minute', 60,),
        ('second', 1,),
    )

    strings = []

    for period_name, period_seconds in periods:
        if round_time:
            period_value, seconds = divmod(seconds, period_seconds)

            if period_value:
                if seconds:
                    period_value += 1

                seconds = 0
            else:
                continue
        else:
            if seconds >= period_seconds:
                period_value, seconds = divmod(seconds, period_seconds)
            else:
                continue

        strings.append(f'{int(period_value)} {period_name}{"s" if period_value > 1 else ""}')

        if only_first or not seconds:
            break

    if not strings:
        strings.append('0 second')

    return ', '.join(strings)


def get_encoded_email(user_email: str) -> str:
    email = user_email.split('@')
    return f'{email[0][:2]}{"*" * len(email[0][2:])}@{email[1]}'
