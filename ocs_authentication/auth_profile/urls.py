from django.conf.urls import url, include

from ocs_authentication.auth_profile.views import AddUpdateUserView


urlpatterns = [
    url(r'^addupdateuser/$', AddUpdateUserView.as_view(), name='add_update_user')
]
