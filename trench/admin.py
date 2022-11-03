from django.contrib import admin

from trench.utils import get_mfa_model


MFAMethod = get_mfa_model()


@admin.register(MFAMethod)
class MFAMethodAdmin(admin.ModelAdmin):
    autocomplete_fields = ['user']
    list_display = ['user', 'name', 'is_primary', 'is_active']
    list_filter = ['name', 'is_primary', 'is_active']
    list_select_related = ['user']
    search_fields = ['user']
