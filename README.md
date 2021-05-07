# django-simple-2fa

## Installation

1. Install the package:
```bash
pip install django-two-factor-auth
```

2. Add in `urls.py`:
```python3
from django.contrib import admin

admin.site.__class__ = AdminSiteWith2FA
```

3. Add settings (an example):
```python3
DJANGO_SIMPLE_2FA = {
    'IS_ENABLED': 'utils.two_factor_auth.two_factor_auth_is_enabled',
    'THROTTLING_IS_ENABLED': 'utils.two_factor_auth.two_factor_auth_throttling_is_enabled',

    'USER_AUTH_SECURITY_CLASS': 'utils.two_factor_auth.CustomUserAuthSecurity',
    'TWO_FACTOR_TYPES': (
        'django_simple_2fa.auth_types.direct.DirectTwoFactorAuthType',
        'utils.two_factor_auth.CustomEmailTwoFactorAuthType',
    ),
    'DEFAULT_TWO_FACTOR_TYPE': 'utils.two_factor_auth.CustomEmailTwoFactorAuthType',
    'USER_TWO_FACTOR_TYPE_GETTER': 'utils.two_factor_auth.get_user_two_factor_auth_type',
}
```
