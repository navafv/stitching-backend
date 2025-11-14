"""
Admin configuration for the 'accounts' app.

Registers the Role and User models with the Django admin site,
providing a customized interface for managing users and roles.
"""

from django.contrib import admin
from .models import Role, User


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin interface customization for the Role model."""
    list_display = ("id", "name", "description")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    Admin interface customization for the custom User model.

    Organizes the user management screen into logical fieldsets
    and provides robust filtering and search capabilities.
    """
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