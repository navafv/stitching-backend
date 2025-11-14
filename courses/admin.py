"""
Admin configuration for the 'courses' app.
"""

from django.contrib import admin
from .models import Course, Trainer, Batch, Enrollment, CourseMaterial


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "duration_weeks", "total_fees", "active", "required_attendance_days")
    list_filter = ("active",)
    search_fields = ("code", "title")
    ordering = ("title",)


@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ("emp_no", "user", "join_date", "salary", "is_active")
    list_filter = ("is_active", "join_date")
    search_fields = ("emp_no", "user__first_name", "user__last_name")
    ordering = ("user__first_name",)
    autocomplete_fields = ['user']


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("code", "course", "trainer", "capacity", "schedule")
    list_filter = ("course", "trainer")
    search_fields = ("code", "course__title", "trainer__user__first_name")
    ordering = ("code",)
    autocomplete_fields = ['course', 'trainer']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "batch", "enrolled_on", "completion_date", "status")
    list_filter = ("status", "batch__course")
    search_fields = ("student__user__first_name", "batch__code")
    readonly_fields = ("enrolled_on", "completion_date")
    ordering = ("-enrolled_on",)
    autocomplete_fields = ['student', 'batch']


@admin.register(CourseMaterial)
class CourseMaterialAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "file", "link", "uploaded_at")
    list_filter = ("course",)
    search_fields = ("title", "description", "course__title")
    ordering = ("-uploaded_at",)
    autocomplete_fields = ['course']