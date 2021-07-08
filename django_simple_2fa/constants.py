from django.utils.translation import gettext_lazy as _


ACCOUNT_ERROR_MSG = _('Username or password is incorrect.')
LAST_ATTEMPT_MSG = _('Last attempt before your account is locked for {blocking_time}.')
ACCOUNT_LOCKED_MSG = _('We\'ve locked you because of too many login attempts. Try again in {waiting_time}.')
