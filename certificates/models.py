from django.db import models
from students.models import Student
from courses.models import Course
from django.utils import timezone
import uuid
from simple_history.models import HistoricalRecords


# -------------------
# CERTIFICATES
# -------------------
class Certificate(models.Model):
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
        unique_together = ("student", "course")
        ordering = ["-issue_date"]

    def __str__(self):
        return f"{self.certificate_no} - {self.student}"

    def save(self, *args, **kwargs):
        # Auto-generate certificate_no if not provided
        if not self.certificate_no:
            today = timezone.now().strftime("%Y%m%d")
            count = Certificate.objects.filter(issue_date__date=timezone.now().date()).count() + 1
            self.certificate_no = f"CERT-{today}-{count:04d}"
        super().save(*args, **kwargs)
