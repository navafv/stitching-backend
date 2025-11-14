"""
Data models for the 'certificates' app.
"""

from django.db import models
from students.models import Student
from courses.models import Course
from django.utils import timezone
import uuid
from simple_history.models import HistoricalRecords


class Certificate(models.Model):
    """
    Represents a certificate of completion issued to a student for a course.
    
    Features:
    - Auto-generates a unique certificate number on save.
    - Auto-generates a UUID for QR code verification.
    - Stores a generated PDF file.
    - Tracks history of changes.
    """
    certificate_no = models.CharField(max_length=30, unique=True, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True)
    issue_date = models.DateField(auto_now_add=True)
    qr_hash = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    remarks = models.CharField(max_length=255, blank=True)
    revoked = models.BooleanField(default=False)
    pdf_file = models.FileField(upload_to="certificates/pdfs/", blank=True, null=True)
    
    history = HistoricalRecords()

    class Meta:
        # A student can only have one non-revoked certificate per course.
        unique_together = ("student", "course") 
        ordering = ["-issue_date"]

    def __str__(self):
        return f"{self.certificate_no} - {self.student}"

    def save(self, *args, **kwargs):
        """
        Auto-generates a unique, sequential certificate number on first save.
        Format: CERT-YYYYMMDD-XXXX
        """
        if not self.certificate_no:
            today = timezone.now().date()
            today_str = today.strftime("%Y%m%d")
            
            # Get count of certificates issued *today* to generate a 
            # sequential number for the day.
            # This is safer than a global count in case of high volume.
            count = Certificate.objects.filter(issue_date=today).count() + 1
            
            self.certificate_no = f"CERT-{today_str}-{count:04d}"
        super().save(*args, **kwargs)