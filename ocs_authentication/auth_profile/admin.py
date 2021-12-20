from django.contrib import admin

from ocs_authentication.auth_profile.models import AuthProfile

class AuthProfileAdmin(admin.ModelAdmin):
    model = AuthProfile
    list_display = ('user', 'staff_view')
    raw_id_fields = ('user',)
    search_fields = ['user__username']

admin.site.register(AuthProfile, AuthProfileAdmin)
