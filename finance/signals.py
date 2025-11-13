"""
Finance Signals
---------------
Triggers fee reminders when overdue conditions are met.
NEW: Generates PDF receipt on creation.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import FeesReceipt, Reminder
from courses.models import Enrollment
from students.models import Student
from django.db.models import Sum

# --- 1. IMPORT PDF UTILS ---
from .utils import generate_receipt_pdf_bytes
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=FeesReceipt)
def handle_fees_receipt_save(sender, instance, created, **kwargs):
    """
    After each receipt is saved:
    1. (On Create) Generate and save the PDF.
    2. Check if the student still owes money.
    """
    
    # --- 2. GENERATE PDF ON CREATE ---
    if created:
        try:
            pdf_bytes = generate_receipt_pdf_bytes(instance.id)
            if pdf_bytes:
                # Save the PDF to the new pdf_file field
                instance.pdf_file.save(
                    f"{instance.receipt_no}.pdf", 
                    ContentFile(pdf_bytes), 
                    save=True # This will re-save the instance
                )
        except Exception as e:
            logger.error(f"Failed to auto-generate PDF for receipt {instance.id}: {e}")

    # --- 3. CHECK FOR OVERDUE FEES (existing logic) ---
    student = instance.student
    course = instance.course

    if not (student and course):
        return

    total_paid = (
        FeesReceipt.objects.filter(student=student, course=course)
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )
    total_due = float(course.total_fees) - float(total_paid)

    if total_due > 0:
        last_reminder = Reminder.objects.filter(student=student, course=course).order_by("-sent_at").first()
        if not last_reminder or (timezone.now() - last_reminder.sent_at).days >= 7:
            Reminder.objects.create(
                student=student,
                course=course,
                batch=instance.batch,
                message=f"Dear {student.user.first_name}, your outstanding fee for {course.title} is ₹{total_due:.2f}. Please pay soon.",
                status="pending",
            )