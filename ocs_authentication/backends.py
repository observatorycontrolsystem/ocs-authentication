from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.contrib.auth.backends import ModelBackend, BaseBackend
from django.core.exceptions import ValidationError, PermissionDenied

from ocs_authentication.util import generate_tokens, get_profile, create_or_update_user
from ocs_authentication.exceptions import ProfileException, OAuthTokenException


class OAuthUsernamePasswordBackend(ModelBackend):
    """
    Authenticate against the OAuth Authorization server using
    grant_type: password

    This backend should be placed after a backend that checks the local database for if the user exists there.
    """
    def authenticate(self, request, username=None, password=None):
        try:
            access_token, refresh_token = generate_tokens(username, password)
        except OAuthTokenException:
            # The authorization server failed to generate tokens. The username and password still might be
            # able to authenticate via another backend, so return `None`.
            return None

        try:
            profile = get_profile(access_token)
        except ProfileException:
            # Failed to get profile data using newly created access token. Something is wrong, indicate not authorized.
            raise PermissionDenied('Failed to access user profile')

        return create_or_update_user(profile, password, access_token, refresh_token)

    def get_user(self, user_id):
        try:
            return get_user_model().objects.get(pk=user_id)
        except get_user_model().DoesNotExist:
            return None


class EmailOrUsernameModelBackend(BaseBackend):
    """
    Authenticate either with username and password, or with email and password.
    """
    def authenticate(self, request, username=None, password=None):
        is_email = True
        try:
            validate_email(username)
        except ValidationError:
            is_email = False
        if is_email:
            kwargs = {'email': username}
        else:
            kwargs = {'username': username}
        try:
            user = get_user_model().objects.get(**kwargs)
            if user.check_password(password):
                return user
        except get_user_model().DoesNotExist:
            return None

    @staticmethod
    def get_user(user_id):
        try:
            return get_user_model().objects.get(pk=user_id)
        except get_user_model().DoesNotExist:
            return None
