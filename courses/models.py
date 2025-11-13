"""
Courses App Models
------------------
Handles Course, Trainer, Batch, and Enrollment relationships.

Improvements:
- Added docstrings, verbose names, and indexes for performance.
- Added validation-ready fields (positive values, constraints).
- Defined Meta options for ordering.
- Ensured referential integrity on all ForeignKeys.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from students.models import Student
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Count


class Course(models.Model):
    """Represents a course offered at the institute."""
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=100)
    duration_weeks = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    total_fees = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    syllabus = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    required_attendance_days = models.PositiveIntegerField(
        default=36, 
        help_text="Total 'Present' days required to complete"
    )

    class Meta:
        ordering = ["title"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["active"]),
        ]
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    def __str__(self):
        return f"{self.title} ({self.code})"


class Trainer(models.Model):
    """
    Represents a trainer/instructor linked to a user account.
    Trainers are staff-level users with additional employment info.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    emp_no = models.CharField(max_length=20, unique=True)
    join_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["user__first_name"]
        indexes = [
            models.Index(fields=["emp_no"]),
            models.Index(fields=["is_active"]),
        ]
        verbose_name = "Trainer"
        verbose_name_plural = "Trainers"

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.emp_no})"


class Batch(models.Model):
    """
    Represents a training "group" or "session" for a specific course.
    Students can be enrolled in this group at any time.
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="batches")
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True, blank=True)
    code = models.CharField(max_length=20, unique=True)
    capacity = models.PositiveIntegerField(default=10, validators=[MinValueValidator(1)])
    schedule = models.JSONField(default=dict, blank=True)  # e.g., {"Mon": "9-11", "Wed": "1-3"}

    class Meta:
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"]),
        ]
        verbose_name = "Batch"
        verbose_name_plural = "Batches"

    def __str__(self):
        return f"{self.course.title} - {self.code}"

    def is_full(self):
        """Returns True if batch capacity is reached."""
        return self.enrollments.count() >= self.capacity


class Enrollment(models.Model):
    """
    Represents a student's enrollment in a batch.
    Stores the individual student's start and completion date.
    """
    STATUS_CHOICES = [
        ("active", "Active"),
        ("completed", "Completed"),
        ("dropped", "Dropped"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollments")
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_on = models.DateField(auto_now_add=True)
    completion_date = models.DateField(null=True, blank=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    class Meta:
        unique_together = ("student", "batch")
        ordering = ["-enrolled_on"]
        indexes = [
            models.Index(fields=["status"]),
        ]
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"

    def __str__(self):
        return f"{self.student.user.get_full_name()} → {self.batch.code}"

    def save(self, *args, **kwargs):
        """
        REMOVED: Automatic calculation of completion_date.
        This is now handled by checking attendance count.
        """
        # (The old logic is removed)
        super().save(*args, **kwargs) # Call the "real" save method.
    
    def get_present_days_count(self):
        """Counts all 'Present' attendance entries for this student in this course."""
        # We check against the course, not the batch, in case the student
        # was moved between batches of the same course.
        return self.student.attendanceentry_set.filter(
            attendance__batch__course=self.batch.course,
            status="P"
        ).count()
    
    def check_and_update_status(self):
        """
        Checks attendance count against course requirement and updates
        status to 'completed' if met.
        """
        if self.status == "active": # Only check active enrollments
            present_count = self.get_present_days_count()
            required_count = self.batch.course.required_attendance_days
            
            if present_count >= required_count:
                self.status = "completed"
                self.completion_date = timezone.now().date() # Set completion date to today
                self.save(update_fields=["status", "completion_date"])


class BatchFeedback(models.Model):
    """
    Stores feedback (rating and comments) from a student
    about a batch they were enrolled in.
    """
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name="feedback")
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comments = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "Batch Feedback"
        verbose_name_plural = "Batch Feedback"

    def __str__(self):
        return f"Feedback for {self.enrollment.batch.code} by {self.enrollment.student.user.get_full_name()}"