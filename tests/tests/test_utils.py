import datetime

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from django_simple_2fa.utils import convert_seconds_to_str, get_encoded_email


UserModel = get_user_model()


class TwoFactorAuthView(APITestCase):
    def test_get_encoded_email(self):
        emails = (
            'test_email@test.com',
            'another_test_email@test.com',
            'one_more_test_email@test.com',
            'yet_test_email@test.com',
            'shit_happens@test.com',
        )
        encoded_emails = (
            'te********@test.com',
            'an****************@test.com',
            'on*****************@test.com',
            'ye************@test.com',
            'sh**********@test.com',
        )

        for email, encoded_email in zip(emails, encoded_emails):
            self.assertEqual(get_encoded_email(email), encoded_email)

    def test_get_encoded_email(self):
        params = (
            datetime.timedelta(minutes=1).total_seconds(),
            datetime.timedelta(minutes=2).total_seconds(),
            datetime.timedelta(hours=3, minutes=2).total_seconds(),
            datetime.timedelta(hours=3, minutes=40).total_seconds(),
            datetime.timedelta(seconds=59).total_seconds(),
            datetime.timedelta(minutes=1, seconds=1).total_seconds(),
        )
        expected_values = (
            '1 minute',
            '2 minutes',
            '3 hours, 2 minutes',
            '3 hours, 40 minutes',
            '59 seconds',
            '1 minute, 1 second',
        )

        for param, expected_value in zip(params, expected_values):
            self.assertEqual(convert_seconds_to_str(int(param)), expected_value)

        expected_values_for_round = (
            '1 minute',
            '2 minutes',
            '4 hours',
            '4 hours',
            '59 seconds',
            '2 minutes',
        )

        for param, expected_value in zip(params, expected_values_for_round):
            self.assertEqual(convert_seconds_to_str(int(param), round_time=True), expected_value)
