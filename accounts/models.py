"""
Accounts App Models
-------------------
Contains Role and custom User models.

Enhancements:
- Added docstrings and Meta options for clarity.
- Added `unique_together` on Role (safety).
- Added verbose names for admin readability.
- Added indexes for faster filtering on role and username.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from simple_history.models import HistoricalRecords


class Role(models.Model):
    """Defines a simple user role (e.g., Admin, Trainer, Student)."""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self) -> str:
        return self.name


class User(AbstractUser):
    """
    Extends Django's built-in AbstractUser with additional fields:
    - role: optional link to Role
    - phone: contact number
    - address: text field for address
    """
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ["username"]
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["email"]),
        ]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return f"{self.username} ({self.role.name if self.role else 'No Role'})"
