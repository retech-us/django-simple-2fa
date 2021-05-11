import datetime
import random
import typing

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import send_mail
from django.template import loader
from django.utils.translation import gettext_lazy as _

from .base import BaseTwoFactorAuthType
from ..dto import TwoFactorAuthObtainResult
from ..errors import TwoFactorAuthError


if typing.TYPE_CHECKING:
    UserModel = get_user_model()

__all__ = (
    'EmailTwoFactorAuthType',
)


class EmailTwoFactorAuthType(BaseTwoFactorAuthType):
    name = 'Email'
    type = 'email'
    _code_ttl = datetime.timedelta(days=1)

    @classmethod
    def obtain(cls, *, user: 'UserModel') -> TwoFactorAuthObtainResult:
        from ..utils import get_encoded_email

        if not user.email:
            raise TwoFactorAuthError('You do not have an email.')

        verification_code = cls._generate_verification_code()

        cache_key = cls._get_cache_key(user)
        cache.set(cache_key, verification_code, cls._code_ttl.total_seconds())

        context = cls.get_context_for_letter(user=user, verification_code=verification_code)
        cls.send_letter(context)

        return TwoFactorAuthObtainResult(
            message=_(
                'A text message with a 6 digit verification code was just sent to {email}. '
                'Please check and enter a code.'
            ).format(
                email=get_encoded_email(user.email),
            ),
            verification_code=verification_code,
        )

    @classmethod
    def reset(cls, *, user: 'UserModel') -> None:
        cache_key = cls._get_cache_key(user)
        cache.delete(cache_key)

    @classmethod
    def is_valid(cls, *,
                 user: 'UserModel',
                 verification_code: str) -> bool:
        cache_key = cls._get_cache_key(user)
        saved_code = cache.get(cache_key)

        code_is_valid = saved_code and verification_code and saved_code == verification_code

        if code_is_valid:
            cls.reset(user=user)

        return code_is_valid

    @staticmethod
    def send_letter(context: dict) -> None:
        message = loader.render_to_string(
            'two_factor_auth/verification_code.txt',
            context=context,
        )

        send_mail(
            subject='2-factor authentication',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[context['user'].email],
        )

    @staticmethod
    def get_context_for_letter(*,
                               user: 'UserModel',
                               verification_code: str) -> dict:
        return {
            'user': user,
            'verification_code': verification_code,
        }

    @staticmethod
    def _get_cache_key(user: 'UserModel') -> str:
        return f'2fa:email:{user.id}'

    @staticmethod
    def _generate_verification_code() -> str:
        return ''.join(map(str, random.choices(range(0, 10), k=6)))
