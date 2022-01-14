import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ocs_authentication.permissions import IsServer
from ocs_authentication.util import create_or_update_user, Profile


class AddUpdateUserView(APIView):
    """
    This view is meant to be called by the Oauth Server when a new user account is created. This will create
    the corresponding user account within this Oauth client app and give it the same api-token, so the user
    can access this application with their api-token without needing to initially login with their password.
    This should also be called on token change or on any user info change.
    """
    permission_classes = [IsServer]

    def post(self, request):
        data = json.loads(request.body.decode('utf-8'))
        profile = Profile(
            data.get('first_name', ''),
            data.get('last_name', ''),
            data.get('username', ''),
            data.get('email', ''),
            data.get('tokens', {}).get('api_token', ''),
            data.get('is_staff', False),
            data.get('is_superuser', False),
            data.get('profile', {}).get('staff_view', False)
        )
        # The password will not be set here since this only has the profile api info.
        # The password will only get set when logging in using username/password auth
        # which is forwarded through Oauth.
        create_or_update_user(profile, password=None)
        return Response({'message': 'User account updated'}, status=status.HTTP_200_OK)
