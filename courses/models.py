"""
Data models for the 'courses' app.

This file defines the core entities related to the institute's curriculum:
- Course: The curriculum itself (e.g., "3 Month Diploma").
- Trainer: An instructor linked to a User account.
- Batch: A specific instance of a Course, taught by a Trainer.
- Enrollment: A link between a Student and a Batch.
- BatchFeedback: A student's review of their enrollment.
- CourseMaterial: Files and links associated with a Course.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from students.models import Student
from django.utils import timezone
from django.db.models import Q, Count


class Course(models.Model):
    """
    Represents a distinct course or program offered by the institute.
    """
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=100)
    duration_weeks = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    total_fees = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    syllabus = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    
    # Defines the number of 'Present' days required to mark the course 'completed'
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
    Represents a trainer/instructor.
    Linked one-to-one with a staff-level User account.
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
    Represents a specific session or group for a Course,
    taught by a Trainer.
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
        """Checks if the number of active enrollments has reached capacity."""
        # Note: You might want to filter this by active enrollments
        return self.enrollments.count() >= self.capacity


class Enrollment(models.Model):
    """
    Associates a Student with a Batch, tracking their status
    (active, completed, dropped).
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
    
    def get_present_days_count(self):
        """
        Counts all 'Present' attendance entries for this student
        for the *entire course*, not just this specific batch.
        """
        return self.student.attendanceentry_set.filter(
            attendance__batch__course=self.batch.course,
            status="P"
        ).count()
    
    def check_and_update_status(self):
        """
        Checks if the student's attendance meets the course requirement.
        If it does, the enrollment is marked as 'completed'.
        
        This logic is triggered from the AttendanceSerializer.
        """
        if self.status == "active": # Only check active enrollments
            present_count = self.get_present_days_count()
            required_count = self.batch.course.required_attendance_days
            
            if present_count >= required_count:
                self.status = "completed"
                self.completion_date = timezone.now().date() # Set completion to today
                self.save(update_fields=["status", "completion_date"])
                # (Future enhancement: trigger certificate creation signal)


class BatchFeedback(models.Model):
    """
    Stores a student's feedback (rating/comments) for a specific
    enrollment, linked One-to-One.
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


class CourseMaterial(models.Model):
    """
    Represents a resource (file or link) associated with a Course.
    Students enrolled in the course can access these materials.
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="materials")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="course_materials/", blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "Course Material"
        verbose_name_plural = "Course Materials"

    def __str__(self):
        return f"{self.title} ({self.course.code})"

    def clean(self):
        """
        Model-level validation to ensure either a file or a link is
        provided, but not both.
        """
        if not self.file and not self.link:
            raise models.ValidationError("Must provide either a file or a link.")
        if self.file and self.link:
            raise models.ValidationError("Cannot provide both a file and a link.")