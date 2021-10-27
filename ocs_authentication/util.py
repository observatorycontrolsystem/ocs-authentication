from dataclasses import dataclass

import requests
from django.db import transaction
from django.contrib.auth import get_user_model

from ocs_authentication.settings import ocs_auth_settings
from ocs_authentication.auth_profile.models import AuthProfile
from ocs_authentication.exceptions import ProfileException, OAuthTokenException


@dataclass
class Profile:
    """Dataclass encapsulating profile information"""
    first_name: str
    last_name: str
    username: str
    email: str
    is_staff: bool
    is_superuser: bool
    staff_view: bool


def get_profile(access_token: str) -> Profile:
    profile_response = requests.get(
        ocs_auth_settings.OAUTH_PROFILE_URL,
        headers={'Authorization': f'Bearer {access_token}'},
        timeout=ocs_auth_settings.REQUESTS_TIMEOUT_SECONDS
    )
    if profile_response.status_code == 200:
        return Profile(
            profile_response.json()['first_name'],
            profile_response.json()['last_name'],
            profile_response.json()['username'],
            profile_response.json()['email'],
            profile_response.json()['is_staff'],
            # TODO: Get actual value of superuser
            profile_response.json()['is_staff'],
            profile_response.json()['profile']['staff_view'],
        )
    else:
        raise ProfileException('Unable to access profile information')


def generate_tokens(username: str, password: str):
    token_response = requests.post(
        ocs_auth_settings.OAUTH_TOKEN_URL,
        data={
            'grant_type': 'password',
            'username': username,
            'password': password,
            'client_id': ocs_auth_settings.OAUTH_CLIENT_ID,
            'client_secret': ocs_auth_settings.OAUTH_CLIENT_SECRET
        },
        timeout=ocs_auth_settings.REQUESTS_TIMEOUT_SECONDS
    )
    if token_response.status_code == 200:
        return token_response.json()['access_token'], token_response.json()['refresh_token']
    else:
        raise OAuthTokenException('Failed to generate OAuth tokens')


def refresh_access_token(refresh_token: str):
    token_response = requests.post(
        ocs_auth_settings.OAUTH_TOKEN_URL,
        data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': ocs_auth_settings.OAUTH_CLIENT_ID,
            'client_secret': ocs_auth_settings.OAUTH_CLIENT_SECRET
        },
        timeout=ocs_auth_settings.REQUESTS_TIMEOUT_SECONDS
    )
    if token_response.status_code == 200:
        return token_response.json()['access_token'], token_response.json()['refresh_token']
    else:
        raise OAuthTokenException('Failed to refresh OAuth tokens')


def revoke_token():
    # TODO: Implement revoking OAuth tokens. This can allow users to revoke a token is their access token
    # is compromised. However, since access tokens are short lived, any compromised access tokens will not
    # work for long, or will not work at all if it is already after the expiration date. If a refresh token
    # is compromised, this is a larger security risk since the refresh token can be used to generate new access
    # and refresh token pairs. However, we do not currently expose refresh tokens to the users.
    # https://django-oauth-toolkit.readthedocs.io/en/latest/tutorial/tutorial_04.html#revoking-a-token
    pass


def create_or_update_user(profile: Profile, password: str, access_token: str, refresh_token: str):
    with transaction.atomic():
        user, _ = get_user_model().objects.update_or_create(
            username=profile.username,
            defaults={
                'first_name': profile.first_name,
                'last_name': profile.last_name,
                'email': profile.email,
                'is_staff': profile.is_staff,
                'is_superuser': profile.is_superuser,
            }
        )
        user.set_password(password)
        user.save()
        AuthProfile.objects.update_or_create(
            user=user,
            defaults={
                'staff_view': profile.staff_view,
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        )
        return user
