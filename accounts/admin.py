"""
Accounts Admin Configuration
----------------------------
Enhancements:
- Added fieldsets for structured admin layout.
- Made critical fields read-only.
- Added search and list filters for performance and usability.
"""

from django.contrib import admin
from .models import Role, User


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "role", "phone", "is_active", "is_staff", "last_login")
    list_filter = ("role", "is_active", "is_staff", "is_superuser")
    search_fields = ("username", "email", "phone", "first_name", "last_name")
    readonly_fields = ("last_login", "date_joined")
    ordering = ("username",)

    fieldsets = (
        ("Basic Info", {"fields": ("username", "email", "password")}),
        ("Personal Details", {"fields": ("first_name", "last_name", "phone", "address")}),
        ("Role & Permissions", {"fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )
