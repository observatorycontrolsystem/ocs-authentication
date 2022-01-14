from django.db import models
from django.conf import settings as django_settings

class AuthProfile(models.Model):
    user = models.OneToOneField(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    staff_view = models.BooleanField(default=False)
    api_token = models.CharField(max_length=255, default='')
