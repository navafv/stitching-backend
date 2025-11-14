"""
Data models for the 'attendance' app.

Defines the Attendance model (a daily record for a batch) and
the AttendanceEntry model (a student's status for that day).
"""

from django.db import models
from django.conf import settings
from students.models import Student
from courses.models import Batch
from django.core.validators import MinLengthValidator


class Attendance(models.Model):
    """
    Represents a single day's attendance sheet for a specific batch.
    """
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="attendance_records")
    date = models.DateField()
    taken_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    remarks = models.TextField(blank=True)

    class Meta:
        unique_together = ("batch", "date") # Only one record per batch per day
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["batch"]),
        ]
        verbose_name = "Attendance"
        verbose_name_plural = "Attendance Records"

    def __str__(self):
        return f"{self.batch.code} - {self.date}"

    @property
    def total_students(self) -> int:
        """Returns the total number of students marked in this attendance."""
        return self.entries.count()

    def summary(self) -> dict:
        """
        Returns a breakdown of attendance counts by status (P/A/L).
        Example: {'P': 10, 'A': 2, 'L': 1}
        """
        counts = self.entries.values("status").order_by("status").annotate(total=models.Count("status"))
        return {c["status"]: c["total"] for c in counts}


class AttendanceEntry(models.Model):
    """
    Represents the status (Present, Absent, Leave) of a single student
    for a specific Attendance record.
    """
    STATUS_CHOICES = [
        ("P", "Present"),
        ("A", "Absent"),
        ("L", "Leave"),
    ]

    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name="entries")
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default="P",
        validators=[MinLengthValidator(1)],
    )

    class Meta:
        unique_together = ("attendance", "student") # Student marked once per sheet
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["student"]),
        ]
        verbose_name = "Attendance Entry"
        verbose_name_plural = "Attendance Entries"

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.get_status_display()}"