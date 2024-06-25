import uuid
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.http import HttpRequest
from rest_framework.test import APITestCase

from django_simple_2fa.auth_types import DirectTwoFactorAuthType
from django_simple_2fa.base import TwoFactorAuth
from django_simple_2fa.dto import TwoFactorRequester
from django_simple_2fa.errors import TwoFactorAuthError
from django_simple_2fa.settings import app_settings


UserModel = get_user_model()


class TwoFactorAuthView(APITestCase):
    def setUp(self):
        self.username = str(uuid.uuid4())
        self.password = '123456'
        self.device_id = str(uuid.uuid4())
        self.user = UserModel(username=self.username, email=f'{self.username}@gmail.com')
        self.user.set_password(self.password)
        self.user.save()

        self.request = HttpRequest()

    @mock.patch.object(app_settings, attribute='IS_ENABLED', new=lambda: True)
    @mock.patch.object(app_settings, attribute='THROTTLING_IS_ENABLED', new=lambda: True)
    def test_status(self):
        cache.clear()

        result = TwoFactorAuth(TwoFactorRequester(
            username=self.username,
            password=self.password,
            device_id=self.device_id,
            ip='127.0.0.1',
            request=self.request,
        )).get_status()

        self.assertIn(result.two_factor_type.type, 'email')

    @mock.patch.object(app_settings, attribute='IS_ENABLED', new=lambda: True)
    @mock.patch.object(app_settings, attribute='THROTTLING_IS_ENABLED', new=lambda: True)
    def test_status_with_invalid_login(self):
        cache.clear()

        for _ in range(3):
            with self.assertRaises(expected_exception=TwoFactorAuthError):
                TwoFactorAuth(TwoFactorRequester(
                    username=str(uuid.uuid4()),
                    password=self.password,
                    device_id=self.device_id,
                    ip='127.0.0.1',
                    request=self.request,
                )).get_status()

        TwoFactorAuth(TwoFactorRequester(
            username=self.username,
            password=self.password,
            device_id=self.device_id,
            ip='127.0.0.1',
            request=self.request,
        )).get_status()

    @mock.patch.object(app_settings, attribute='IS_ENABLED', new=lambda: False)
    @mock.patch.object(app_settings, attribute='THROTTLING_IS_ENABLED', new=lambda: True)
    def test_status_without_2fa(self):
        cache.clear()

        result = TwoFactorAuth(TwoFactorRequester(
            username=self.username,
            password=self.password,
            device_id=self.device_id,
            ip='127.0.0.1',
            request=self.request,
        )).get_status()

        self.assertIn(result.two_factor_type.type, DirectTwoFactorAuthType.type)

    # @override_config(ENABLE_TWO_FACTOR_AUTH=True, ENABLE_IP_THROTTLING=True)
    # def test_status_without_user_2fa(self):
    #     cache.clear()
    #
    #     self.user.profile.two_factor_auth_type = DirectTwoFactorAuthType.type
    #     self.user.profile.save(update_fields=('two_factor_auth_type',))
    #
    #     result = TwoFactorAuth(TwoFactorRequester(
    #         username=self.username,
    #         password=self.password,
    #         device_id=self.device_id,
    #         ip='127.0.0.1',
    #     )).get_status()
    #
    #     self.assertIn(result.two_factor_type.type, DirectTwoFactorAuthType.type)

    @mock.patch.object(app_settings, attribute='IS_ENABLED', new=lambda: True)
    @mock.patch.object(app_settings, attribute='THROTTLING_IS_ENABLED', new=lambda: True)
    def test_obtain(self):
        cache.clear()

        with mock.patch.object(EmailMultiAlternatives, 'send') as mocked_send_mail:
            result = TwoFactorAuth(TwoFactorRequester(
                username=self.username,
                password=self.password,
                device_id=self.device_id,
                ip='127.0.0.1',
                request=self.request,
            )).obtain()

        self.assertTrue(mocked_send_mail.called)
        self.assertTrue(result.message)

    @mock.patch.object(app_settings, attribute='IS_ENABLED', new=lambda: True)
    @mock.patch.object(app_settings, attribute='THROTTLING_IS_ENABLED', new=lambda: True)
    def test_obtain_with_few_attempts(self):
        cache.clear()

        for _ in range(3):
            with self.assertRaises(expected_exception=TwoFactorAuthError):
                TwoFactorAuth(TwoFactorRequester(
                    username=self.username,
                    password=str(uuid.uuid4()),
                    device_id=self.device_id,
                    ip='127.0.0.1',
                    request=self.request,
                )).obtain()

        with self.assertRaises(expected_exception=TwoFactorAuthError):
            TwoFactorAuth(TwoFactorRequester(
                username=self.username,
                password=self.password,
                device_id=self.device_id,
                ip='127.0.0.1',
                request=self.request,
            )).obtain()

    @mock.patch.object(app_settings, attribute='IS_ENABLED', new=lambda: True)
    @mock.patch.object(app_settings, attribute='THROTTLING_IS_ENABLED', new=lambda: True)
    def test_verify(self):
        cache.clear()

        message: str = ''

        def _mocked_send(self):
            nonlocal message
            message = self.body

        with mock.patch.object(EmailMultiAlternatives, 'send', new=_mocked_send):
            TwoFactorAuth(TwoFactorRequester(
                username=self.username,
                password=self.password,
                device_id=self.device_id,
                ip='127.0.0.1',
                request=self.request,
            )).obtain()

        phrase = 'verification code '
        start_position = message.index(phrase) + len(phrase)
        verification_code = message[start_position:start_position + 6]

        response = TwoFactorAuth(TwoFactorRequester(
            username=self.username,
            password=self.password,
            device_id=self.device_id,
            ip='127.0.0.1',
            request=self.request,
        )).verify(verification_code)

        self.assertEqual(response.user, self.user)

    @mock.patch.object(app_settings, attribute='IS_ENABLED', new=lambda: False)
    @mock.patch.object(app_settings, attribute='THROTTLING_IS_ENABLED', new=lambda: True)
    def test_verify_without_2fa(self):
        cache.clear()

        response = TwoFactorAuth(TwoFactorRequester(
            username=self.username,
            password=self.password,
            device_id=self.device_id,
            ip='127.0.0.1',
            request=self.request,
        )).verify('')

        self.assertEqual(response.user, self.user)
