from django.urls import re_path

from ocs_authentication.auth_profile.views import AddUpdateUserView


urlpatterns = [
    re_path(r'^addupdateuser/$', AddUpdateUserView.as_view(), name='add_update_user')
]
