from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.contrib.auth.backends import ModelBackend, BaseBackend
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils.translation import gettext as _
from rest_framework.authentication import TokenAuthentication, exceptions
from ocs_authentication.util import generate_tokens, get_profile, create_or_update_user
from ocs_authentication.auth_profile.models import AuthProfile
from ocs_authentication.exceptions import ProfileException, OAuthTokenException


class OCSTokenAuthentication(TokenAuthentication):
    """
    This Allows authentication based on the api_key stored in the AuthProfile model.
    This should allow users to use the same api_key between client apps and the Oauth Server.
    TODO:: Once we switch to just using the DRF tokens rather than allowing both DRF tokens and
           the AuthProfile api_tokens, this backend should no longer be necessary.
    """
    def authenticate_credentials(self, key):
        try:
            output = super().authenticate_credentials(key)
            return output
        except exceptions.AuthenticationFailed:
            pass
        # Fallback on trying the api_token in the AuthToken model
        try:
            token = AuthProfile.objects.select_related('user').get(api_token=key)
        except AuthProfile.DoesNotExist:
            raise exceptions.AuthenticationFailed(_('Invalid token.'))

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed(_('User inactive or deleted.'))

        return (token.user, token)


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
            profile = get_profile(access_token=access_token)
        except ProfileException:
            # Failed to get profile data using newly created access token. Something is wrong, indicate not authorized.
            raise PermissionDenied('Failed to access user profile')

        return create_or_update_user(profile, password)

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
