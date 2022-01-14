from copy import deepcopy
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model


class MockResponse:
    def __init__(self, data, status_code) -> None:
        self.data = data
        self.status_code = status_code
    
    def json(self):
        return self.data


@patch('ocs_authentication.util.requests.post')
@patch('ocs_authentication.util.requests.get')
@override_settings(
    AUTHENTICATION_BACKENDS=[
       'ocs_authentication.backends.EmailOrUsernameModelBackend',
       'ocs_authentication.backends.OAuthUsernamePasswordBackend'
    ],
    OCS_AUTHENTICATION={
        'OAUTH_TOKEN_URL': 'localhost',
        'OAUTH_PROFILE_URL': 'localhost'
    }
)
class TestOauthUsernamePasswordAuth(TestCase):
    def setUp(self) -> None:
        self.profile_response = {
            'username': 'jdoe',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jdoe@example.com',
            'profile': {
                'staff_view': False,
            },
            'tokens': {
                'api_token': '1234'
            },
            'is_staff': False,
            'is_superuser': False
        }
        password = 'qwerty'
        self.token_response = {
            'access_token': '123456',
            'refresh_token': '246810'
        }
        self.username_credentials = {
            'username': self.profile_response['username'],
            'password': password
        }
        self.email_credentials = {
            'username': self.profile_response['email'],
            'password': password
        }

    def check_user(self, user, profile_response=None, token_response=None):
        if profile_response is None:
            profile_response = self.profile_response
        if token_response is None:
            token_response = self.token_response
        self.assertEqual(user.authprofile.staff_view, profile_response['profile']['staff_view'])
        self.assertEqual(user.is_staff, profile_response['is_staff'])
        self.assertEqual(user.first_name, profile_response['first_name'])
        self.assertEqual(user.last_name, profile_response['last_name'])
        self.assertEqual(user.username, profile_response['username'])
        self.assertEqual(user.email, profile_response['email'])

    def test_log_in_successful(self, mock_get, mock_post):
        mock_get.return_value = MockResponse(self.profile_response, 200)
        mock_post.return_value = MockResponse(self.token_response, 200)
        # First check that the user does not exist
        self.assertEqual(get_user_model().objects.filter(username=self.profile_response['username']).count(), 0)
        for credentials in [self.username_credentials, self.email_credentials]:
            with self.subTest(credentials=credentials):
                logged_in = self.client.login(**credentials)
                self.assertTrue(logged_in)
                # After logging in, the user should exist along with access and refresh tokens
                user_queryset = get_user_model().objects.filter(username=self.profile_response['username'])
                self.assertEqual(user_queryset.count(), 1)
                self.check_user(user_queryset.first())
    
    def test_log_in_staff_user_has_is_staff_set(self, mock_get, mock_post):
        profile_response = deepcopy(self.profile_response)
        profile_response['is_staff'] = True
        mock_get.return_value = MockResponse(profile_response, 200)
        mock_post.return_value = MockResponse(self.token_response, 200)
        user_queryset = get_user_model().objects.filter(username=self.profile_response['username'])
        self.assertEqual(user_queryset.count(), 0)
        logged_in = self.client.login(**self.username_credentials)
        self.assertTrue(logged_in)
        self.assertEqual(user_queryset.count(), 1)
        self.check_user(user_queryset.first(), profile_response=profile_response)

    def test_log_in_staff_user_with_staff_view_has_is_staff_and_staff_view_set(self, mock_get, mock_post):
        profile_response = deepcopy(self.profile_response)
        profile_response['is_staff'] = True
        profile_response['profile']['staff_view'] = True
        mock_get.return_value = MockResponse(profile_response, 200)
        mock_post.return_value = MockResponse(self.token_response, 200)
        user_queryset = get_user_model().objects.filter(username=self.profile_response['username'])
        self.assertEqual(user_queryset.count(), 0)
        logged_in = self.client.login(**self.username_credentials)
        self.assertTrue(logged_in)
        self.assertEqual(user_queryset.count(), 1)
        self.check_user(user_queryset.first(), profile_response=profile_response)

    def test_incorrect_login_credentials_fails(self, mock_get, mock_post):
        mock_post.return_value = MockResponse({}, 403)
        logged_in = self.client.login(**self.username_credentials)
        self.assertFalse(logged_in)
        self.assertEqual(get_user_model().objects.filter(username=self.username_credentials['username']).count(), 0)

    def test_log_in_multiple_times_only_creates_one_set_of_tokens(self, mock_get, mock_post):
        mock_get.side_effect = [MockResponse(self.profile_response, 200)]
        mock_post.side_effect = [MockResponse(self.token_response, 200)]
        # First check that the user does not exist
        user_queryset = get_user_model().objects.filter(username=self.profile_response['username'])
        self.assertEqual(user_queryset.count(), 0)
        # Log in one time, after the first time a user should be created
        logged_in = self.client.login(**self.username_credentials)
        self.assertTrue(logged_in)
        self.assertEqual(user_queryset.count(), 1)
        self.check_user(user_queryset.first())
        # Log in another time. This time the user already exists in the system, so that user is returned and
        # tokens are not regenerated.
        logged_in = self.client.login(**self.username_credentials)
        self.assertTrue(logged_in)
        self.assertEqual(user_queryset.count(), 1)
        self.check_user(user_queryset.first())
        # Log in one more time using email and password this time. The user still exists in the system.
        logged_in = self.client.login(**self.email_credentials)
        self.assertTrue(logged_in)
        self.assertEqual(user_queryset.count(), 1)
        self.check_user(user_queryset.first())
        # Token generation and profile access should only have happened one time across these three separate logins
        mock_post.assert_called_once()
        mock_get.assert_called_once()

    def test_log_in_fails_when_token_generation_fails(self, mock_get, mock_post):
        mock_post.return_value = MockResponse({}, 500)
        user_queryset = get_user_model().objects.filter(username=self.profile_response['username'])
        self.assertEqual(user_queryset.count(), 0)
        logged_in = self.client.login(**self.username_credentials)
        self.assertFalse(logged_in)
        self.assertEqual(user_queryset.count(), 0)
    
    def test_log_in_fails_when_getting_profile_fails(self, mock_get, mock_post):
        mock_get.return_value = MockResponse({}, 500)
        mock_post.return_value = MockResponse(self.token_response, 200)
        user_queryset = get_user_model().objects.filter(username=self.profile_response['username'])
        self.assertEqual(user_queryset.count(), 0)
        logged_in = self.client.login(**self.username_credentials)
        self.assertFalse(logged_in)
        self.assertEqual(user_queryset.count(), 0)


@override_settings(
    AUTHENTICATION_BACKENDS=[
       'ocs_authentication.backends.EmailOrUsernameModelBackend'
    ]
)
class TestEmailOrUsernameModelBackend(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.username = 'jane'
        cls.email = 'jdoe@example.com'
        cls.password = 'supersecret'
        cls.user = get_user_model().objects.create(username=cls.username, email=cls.email)
        cls.user.set_password(cls.password)
        cls.user.save()

    def test_log_in_with_username_succeeds(self):
        logged_in = self.client.login(username=self.username, password=self.password)
        self.assertTrue(logged_in)

    def test_log_in_with_email_succeeds(self):
        logged_in = self.client.login(username=self.email, password=self.password)
        self.assertTrue(logged_in)
    
    def test_log_in_with_invalid_email_fails(self):
        logged_in = self.client.login(username='invalid@example.com', password=self.password)
        self.assertFalse(logged_in)

    def test_log_in_with_invalid_username_fails(self):
        logged_in = self.client.login(username='janet', password=self.password)
        self.assertFalse(logged_in)

    def test_log_in_with_invalid_password_fails(self):
        logged_in = self.client.login(username=self.username, password='wrongpass')
        self.assertFalse(logged_in)
