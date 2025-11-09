"""
Attendance Admin
----------------
Enhancements:
- Inline entries for easier marking.
- Filter and search improvements.
"""

from django.contrib import admin
from .models import Attendance, AttendanceEntry


class AttendanceEntryInline(admin.TabularInline):
    model = AttendanceEntry
    extra = 0
    autocomplete_fields = ["student"]
    readonly_fields = []


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("batch", "date", "taken_by", "total_students", "remarks")
    list_filter = ("date", "batch__course", "batch")
    search_fields = ("batch__code", "remarks")
    inlines = [AttendanceEntryInline]
    ordering = ("-date",)

    @admin.display(description="Total Students")
    def total_students(self, obj):
        return obj.total_students
