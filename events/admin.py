"""
Admin configuration for the 'events' app.
"""

from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'created_by', 'created_at')
    list_filter = ('start_date', 'created_by')
    search_fields = ('title', 'description')
    
    # These fields are set automatically
    readonly_fields = ('created_at', 'created_by')
    
    autocomplete_fields = ['created_by']

    def save_model(self, request, obj, form, change):
        """
        When an event is created in the admin,
        assign the current user as the creator.
        """
        if not obj.pk: # Only on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)