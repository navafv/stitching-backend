"""
Attendance App Models
---------------------
Tracks daily attendance for batches and their students.

Enhancements:
- Added indexes for performance on date, batch, and status.
- Added verbose names and Meta options.
- Added helper methods for summary counts.
- Enforced constraints for consistency.
"""

from django.db import models
from django.conf import settings
from students.models import Student
from courses.models import Batch
from django.core.validators import MinLengthValidator


class Attendance(models.Model):
    """Represents the attendance record for a specific batch on a specific date."""
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="attendance_records")
    date = models.DateField()
    taken_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    remarks = models.TextField(blank=True)

    class Meta:
        unique_together = ("batch", "date")
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
        """Returns total number of students marked in this attendance."""
        return self.entries.count()

    def summary(self) -> dict:
        """Returns a breakdown of attendance by status (P/A/L)."""
        counts = self.entries.values("status").order_by("status").annotate(total=models.Count("status"))
        return {c["status"]: c["total"] for c in counts}


class AttendanceEntry(models.Model):
    """Represents the attendance status of a single student in a batch."""
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
        unique_together = ("attendance", "student")
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["student"]),
        ]
        verbose_name = "Attendance Entry"
        verbose_name_plural = "Attendance Entries"

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.get_status_display()}"
