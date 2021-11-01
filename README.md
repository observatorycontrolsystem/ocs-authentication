# OCS Authentication

Authentication backends and utilities for the OCS.

For the OCS, the authorization server is the Observation Portal.

## Installation and Getting Started

To install the library into your Django application:
```
pip install ocs-authentication
```

Add the following to your Django project's `INSTALLED_APPS` to add the `AuthProfile` app to you project. This app is needed if any backends that use OAuth are used, which create user accounts that are meant to mirror accounts in the authorization server:

```
INSTALLED_APPS = [
    ...
    'ocs_authentication.auth_profile',
    ...
]
```
Then, run migrations to create the `AuthProfile` objects:
```
python manage.py migrate
```

Then you can configure the authentication backends. See the [Authentication Backends](#authentication-backends) section.

## Authentication Backends

You may need to clear out current sessions when updating the authentication backends in your project. From the [Django documentation](https://docs.djangoproject.com/en/3.2/topics/auth/customizing/#specifying-authentication-backends):

> Once a user has authenticated, Django stores which backend was used to authenticate the user in the user’s session, and re-uses the same backend for the duration of that session whenever access to the currently authenticated user is needed. This effectively means that authentication sources are cached on a per-session basis, so if you change AUTHENTICATION_BACKENDS, you’ll need to clear out session data if you need to force users to re-authenticate using different methods. A simple way to do that is to execute `Session.objects.all().delete()`.

### EmailOrUsernameModelBackend

This backend is similar to Django's `django.contrib.auth.backends.ModelBackend`, except that it allows a user to log in with either their username or email, not just with their username. To add to your project:
```
AUTHENTICATION_BACKENDS = [
    ...
    'ocs_authentication.backends.EmailOrUsernameModelBackend',
    ...
]
```

### OAuthUsernamePasswordBackend

This backend allows a user to authenticate using username and password with the OAuth authorization server. This backend checks whether the user account exists in the authorization server, and if it does, creates or updates that user account locally. If the intention is to check the local database first for if the user exists before sending a call off to the authorization server, you must add either `ocs_authentication.backends.EmailOrUsernameModelBackend` or `django.contrib.auth.backends.ModelBackend` to the `AUTHENTICATION_BACKENDS` *before* this backend is listed.
```
AUTHENTICATION_BACKENDS = [
     ...
    # 'ocs_authentication.backends.EmailOrUsernameModelBackend', # Add this to check local DB first
    'ocs_authentication.backends.OAuthUsernamePasswordBackend',
    ...
]
```

Note that if the you want to check the local DB for if the user exists there first, choose either `EmailOrUsernameModelBackend` or `ModelBackend` based on which of these backends is used in the authorization server. Using `EmailOrUsernameModelBackend` in the authorization server but using `ModelBackend` in the client application will mean that any time a user logs in to the client app with their email, the authentication request will always be forwarded to the authorization server even if the user account already exists in the local DB.

## Settings

All settings for this library are namespaced under the `OCS_AUTHENTICATION` dictionary. In your settings file:
```
OCS_AUTHENTICATION = {
    # Your settings go here
}
```

### OAUTH_TOKEN_URL
Default: `''`

The token url of the authorization server, usually the Observation Portal's `/o/token/` endpoint.

### OAUTH_PROFILE_URL
Default: `''`

The URL from which to retrieve user information, which is the Observation Portal's `/api/profile/` endpoint.

### OAUTH_CLIENT_ID
Default: `''`

The OAuth client ID for the OAuth application in the authorization server used to generate tokens via username and password.

### OAUTH_CLIENT_SECRET
Default: `''`

The OAuth client secret for the OAuth application in the authorization server used to generate tokens via username and password.

### REQUESTS_TIMEOUT_SECONDS
Default: `60`

The timeout for remote network calls.
