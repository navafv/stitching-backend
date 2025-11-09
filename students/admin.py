"""
Students Admin
--------------
Enhancements:
- Readable admin list view.
- Filters and search fields optimized for common lookups.
"""

from django.contrib import admin
from .models import Enquiry, Student


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "phone", "course_interest", "status", "created_at")
    list_filter = ("status", "course_interest")
    search_fields = ("name", "phone", "email", "notes")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("reg_no", "user", "guardian_name", "guardian_phone", "admission_date", "active")
    list_filter = ("active", "admission_date")
    search_fields = (
        "reg_no",
        "user__first_name",
        "user__last_name",
        "guardian_name",
        "guardian_phone",
    )
    readonly_fields = ("reg_no",)
    ordering = ("-admission_date",)
