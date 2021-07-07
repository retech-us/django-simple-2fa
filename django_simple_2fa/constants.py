from django.utils.translation import gettext_lazy as _


ACCOUNT_ERROR_MSG = _('Username or password are incorrect.')
LAST_ATTEMPT_MSG = _('1 attempt before your account is locked for a few minutes.')
ACCOUNT_LOCKED_MSG = _('We\'ve locked you because of too many login attempts. Try again in {waiting_time}.')
