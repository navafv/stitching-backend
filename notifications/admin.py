"""
Admin configuration for the 'notifications' app.
"""

from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "level", "is_read", "created_at")
    list_filter = ("level", "is_read", "created_at")
    search_fields = ("title", "message", "user__username")
    readonly_fields = ("created_at",)
    autocomplete_fields = ['user']