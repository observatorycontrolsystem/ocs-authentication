from django.conf import settings as django_settings
from django.core.signals import setting_changed


DEFAULT_SETTINGS = {
    'OAUTH_TOKEN_URL': '',
    'OAUTH_PROFILE_URL': '',
    'OAUTH_CLIENT_ID': '',
    'OAUTH_CLIENT_SECRET': '',
    'OAUTH_SERVER_KEY': '',
    'REQUESTS_TIMEOUT_SECONDS': 60
}


class OCSAuthSettings:
    namespace = 'OCS_AUTHENTICATION'

    def __init__(self, default_settings=None) -> None:
        self.default_settings = DEFAULT_SETTINGS if default_settings is None else default_settings
        self._cached_settings = set()
        self.load()

    def load(self) -> None:
        # Clear out the current settings - they will be replaced
        for setting in self._cached_settings:
            if hasattr(self, setting):
                delattr(self, setting)
        self._cached_settings.clear()
        # Set the settings
        user_specified_settings = getattr(django_settings, self.namespace, {})
        for setting in self.default_settings:
            if setting in user_specified_settings:
                setattr(self, setting, user_specified_settings[setting])
            else:
                setattr(self, setting, self.default_settings[setting])
            self._cached_settings.add(setting)


ocs_auth_settings = OCSAuthSettings()


def reload_settings(*args, **kwargs):
    setting = kwargs.get('setting')
    if setting == OCSAuthSettings.namespace:
        ocs_auth_settings.load()


setting_changed.connect(reload_settings)
