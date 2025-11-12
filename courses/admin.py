"""
Courses Admin
-------------
Enhancements:
- Added filters, search fields, and read-only safety.
- Improved display and ordering.
"""

from django.contrib import admin
from .models import Course, Trainer, Batch, Enrollment


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "duration_weeks", "total_fees", "active")
    list_filter = ("active",)
    search_fields = ("code", "title")
    ordering = ("title",)
    prepopulated_fields = {"code": ("title",)}


@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ("emp_no", "user", "join_date", "salary", "is_active")
    list_filter = ("is_active", "join_date")
    search_fields = ("emp_no", "user__first_name", "user__last_name")
    ordering = ("user__first_name",)


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("code", "course", "trainer", "capacity", "schedule")
    list_filter = ("course", "trainer")
    search_fields = ("code", "course__title", "trainer__user__first_name")
    ordering = ("code",)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "batch", "enrolled_on", "completion_date", "status")
    list_filter = ("status", "batch__course")
    search_fields = ("student__user__first_name", "batch__code")
    readonly_fields = ("enrolled_on", "completion_date")
    ordering = ("-enrolled_on",)
