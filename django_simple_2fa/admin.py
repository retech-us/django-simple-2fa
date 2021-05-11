import datetime
import uuid

from django import forms
from django.contrib.admin import AdminSite
from django.contrib.admin.forms import AdminAuthenticationForm
from django.utils.translation import gettext_lazy as _

from .auth_types import DirectTwoFactorAuthType
from .base import TwoFactorAuth
from .dto import TwoFactorRequester
from .errors import TwoFactorAuthError
from .utils import get_ip_from_request


__all__ = (
    'AdminAuthenticationFormWith2FA',
    'AdminSiteWith2FA',
)


class AdminAuthenticationFormWith2FA(AdminAuthenticationForm):
    verification_code = forms.CharField(
        label=_('Verification code from email'),
        widget=forms.TextInput(),
        required=False,
    )
    password = forms.CharField(
        label=_('Password'),
        strip=False,
        widget=forms.PasswordInput(
            render_value=True,
            attrs={'autocomplete': 'current-password'},
        ),
    )

    def clean(self):
        requester = TwoFactorRequester(
            username=self.cleaned_data.get('username'),
            password=self.cleaned_data.get('password'),
            device_id=self.request.COOKIES.get('device_id', str(uuid.uuid4())),
            ip=get_ip_from_request(self.request),
        )

        two_factor_auth_service = TwoFactorAuth(requester)

        verification_code = self.cleaned_data.get('verification_code')

        try:
            status = two_factor_auth_service.get_status()
        except TwoFactorAuthError as e:
            raise forms.ValidationError(e.reason)

        if verification_code or issubclass(status.two_factor_type, DirectTwoFactorAuthType):
            try:
                two_factor_auth_service.verify(verification_code)
            except TwoFactorAuthError as e:
                raise forms.ValidationError(e.reason)
        else:
            try:
                result = two_factor_auth_service.obtain()
            except TwoFactorAuthError as e:
                raise forms.ValidationError(e.reason)
            else:
                raise forms.ValidationError(result.message)

        return super().clean()


class AdminSiteWith2FA(AdminSite):
    """
    Mixin for enforcing OTP verified staff users.
    Custom admin views should either be wrapped using :meth:`admin_view` or
    use :meth:`has_permission` in order to secure those views.
    """
    login_form = AdminAuthenticationFormWith2FA
    login_template = 'two_factor_auth/admin_login.html'

    def login(self, request, *args, **kwargs):
        response = super().login(request, *args, **kwargs)
        device_id = request.COOKIES.get('device_id')

        if not device_id:
            device_id = str(uuid.uuid4())
            response.set_cookie(
                'device_id',
                device_id,
                max_age=datetime.timedelta(days=365).total_seconds(),
                secure=True,
                httponly=False,  # FE also can use it.
            )

        return response
