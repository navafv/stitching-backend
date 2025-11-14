"""
Data models for the 'accounts' app.

Defines the Role and custom User models, extending Django's
authentication system to include role-based access control and
additional user profile information.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from simple_history.models import HistoricalRecords


class Role(models.Model):
    """
    Defines a user role within the system (e.g., Admin, Trainer, Student).
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    history = HistoricalRecords() # Tracks changes to Role instances

    class Meta:
        ordering = ["name"]
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self) -> str:
        return self.name
    
    def get_user_ids(self):
        """Helper to retrieve all user IDs associated with this role."""
        return list(self.user_set.values_list('id', flat=True))


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.

    Adds role-based permissions and basic contact info.
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