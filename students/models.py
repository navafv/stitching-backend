"""
Students App Models
-------------------
Handles student registrations and enquiries.

Enhancements:
- Added verbose names, ordering, and indexes for faster lookups.
- Added optional auto reg_no generator helper.
- Ensured timezone-safe default for admission_date.
"""

from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.validators import RegexValidator
from simple_history.models import HistoricalRecords


class Enquiry(models.Model):
    """Represents a new student enquiry (pre-admission)."""
    STATUS_CHOICES = [
        ("new", "New"),
        ("follow_up", "Follow Up"),
        ("converted", "Converted"),
        ("closed", "Closed"),
    ]

    name = models.CharField(max_length=100)
    phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(r"^[0-9+() -]+$", "Invalid phone number format.")],
    )
    email = models.EmailField(blank=True)
    course_interest = models.CharField(max_length=100)
    source = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Enquiry"
        verbose_name_plural = "Enquiries"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["course_interest"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_status_display()})"


class Student(models.Model):
    """
    Represents a registered student.
    One-to-one with User for account access.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reg_no = models.CharField(max_length=30, unique=True)
    guardian_name = models.CharField(max_length=100)
    guardian_phone = models.CharField(max_length=15)
    admission_date = models.DateField(default=timezone.localdate)
    address = models.TextField(blank=True)
    photo = models.ImageField(upload_to="students/photos/", blank=True, null=True)
    active = models.BooleanField(default=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ["-admission_date", "reg_no"]
        indexes = [
            models.Index(fields=["reg_no"]),
            models.Index(fields=["active"]),
        ]
        verbose_name = "Student"
        verbose_name_plural = "Students"

    def __str__(self) -> str:
        return f"{self.user.get_full_name()} ({self.reg_no})"

    # Example: helper to auto-generate reg_no
    @staticmethod
    def generate_reg_no() -> str:
        """Generates a simple registration number like STU2025-001."""
        count = Student.objects.count() + 1
        year = timezone.now().year
        return f"STU{year}-{count:03d}"
