"""
Admin configuration for the 'attendance' app.
"""

from django.contrib import admin
from .models import Attendance, AttendanceEntry


class AttendanceEntryInline(admin.TabularInline):
    """
    Inline admin for AttendanceEntry.
    Allows for marking attendance directly within the Attendance admin page.
    """
    model = AttendanceEntry
    extra = 0 # Don't show extra empty forms by default
    autocomplete_fields = ["student"]
    readonly_fields = []


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """Admin interface customization for the Attendance model."""
    list_display = ("batch", "date", "taken_by", "get_total_students", "remarks")
    list_filter = ("date", "batch__course", "batch")
    search_fields = ("batch__code", "remarks")
    inlines = [AttendanceEntryInline]
    ordering = ("-date",)
    autocomplete_fields = ['batch', 'taken_by']
    
    @admin.display(description="Total Students")
    def get_total_students(self, obj):
        """Calculated field for the list display."""
        return obj.total_students