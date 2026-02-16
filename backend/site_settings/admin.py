from django.contrib import admin
from .models import SiteSetting


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'name', 'type', 'is_active', 'updated_at']
    list_filter = ['type', 'is_active']
    search_fields = ['key', 'name']