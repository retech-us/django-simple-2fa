from django.conf import settings
from django.test.signals import setting_changed
from rest_framework.settings import APISettings as _APISettings


USER_SETTINGS = getattr(settings, 'DJANGO_SIMPLE_2FA', None)

DEFAULTS = {
    'IS_ENABLED': None,
    'THROTTLING_IS_ENABLED': None,

    'USER_AUTH_SECURITY_CLASS': 'django_simple_2fa.utils.UserAuthSecurity',
    'TWO_FACTOR_TYPES': (
        'django_simple_2fa.auth_types.direct.DirectTwoFactorAuthType',
        'django_simple_2fa.auth_types.email.EmailTwoFactorAuthType',
    ),
    'DEFAULT_TWO_FACTOR_TYPE': 'django_simple_2fa.auth_types.email.EmailTwoFactorAuthType',
    'USER_TWO_FACTOR_TYPE_GETTER': None,

    'RATE_THROTTLE_FOR_AUTH': 'django_simple_2fa.throttling.rate_throttle_for_auth',
    'RATE_THROTTLE_FOR_OBTAIN': 'django_simple_2fa.throttling.rate_throttle_for_obtain',
    'RATE_THROTTLE_FOR_VERIFY': 'django_simple_2fa.throttling.rate_throttle_for_verify',
}

IMPORT_STRINGS = (
    'IS_ENABLED',
    'THROTTLING_IS_ENABLED',

    'USER_AUTH_SECURITY_CLASS',
    'TWO_FACTOR_TYPES',
    'DEFAULT_TWO_FACTOR_TYPE',

    'USER_TWO_FACTOR_TYPE_GETTER',

    'RATE_THROTTLE_FOR_AUTH',
    'RATE_THROTTLE_FOR_OBTAIN',
    'RATE_THROTTLE_FOR_VERIFY',
)


class APPSettings(_APISettings):
    def __getattr__(self, attr):
        if attr == 'TWO_FACTOR_TYPES_MAP':
            val = {
                two_factor_type.type: two_factor_type
                for two_factor_type in self.TWO_FACTOR_TYPES
            }

            # Cache the result
            self._cached_attrs.add(attr)
            setattr(self, attr, val)
            return val

        if attr == 'TWO_FACTOR_TYPES_CHOICES':
            val = (
                (two_factor_type.type, two_factor_type.name,)
                for two_factor_type in self.TWO_FACTOR_TYPES
            )

            # Cache the result
            self._cached_attrs.add(attr)
            setattr(self, attr, val)
            return val

        return super().__getattr__(attr)


app_settings = APPSettings(USER_SETTINGS, DEFAULTS, IMPORT_STRINGS)


def reload_app_settings(*args, **kwargs):
    global app_settings

    setting, value = kwargs['setting'], kwargs['value']

    if setting == 'DJANGO_SIMPLE_2FA':
        app_settings = APPSettings(value, DEFAULTS, IMPORT_STRINGS)


setting_changed.connect(reload_app_settings)
