from django.contrib import admin

from trench.models import MFAMethod


@admin.register(MFAMethod)
class MFAMethodAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user", "is_primary", "is_active")
    list_filter = ("name", "is_primary", "is_active")
    pass
