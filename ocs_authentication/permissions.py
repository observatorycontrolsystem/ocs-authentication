
from rest_framework import permissions
from django.conf import settings


class IsAdminOrReadOnly(permissions.BasePermission):
    """The request is either read-only, or the user is staff"""
    def has_permission(self, request, view):
        return bool(
            request.method in permissions.SAFE_METHODS
            or request.user and request.user.is_staff
        )


class IsServer(permissions.BasePermission):
    message = 'Invalid or missing API Key.'

    def has_permission(self, request, view):
        authorization = request.META.get("HTTP_AUTHORIZATION")

        key = ''
        if authorization:
            try:
                _, key = authorization.split("Server ")
            except ValueError:
                pass

        if key:
            return key == settings.OCS_AUTHENTICATION['OAUTH_SERVER_KEY']

        return False
