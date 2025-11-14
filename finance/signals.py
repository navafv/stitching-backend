"""
Signal handlers for the 'finance' app.

This file connects functions to model events, such as:
- Automatically generating a PDF when a FeesReceipt is created.
- Triggering a fee reminder check when a receipt is saved.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import FeesReceipt, Reminder
from courses.models import Enrollment
from students.models import Student
from django.db.models import Sum
from .utils import generate_receipt_pdf_bytes
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=FeesReceipt)
def handle_fees_receipt_save(sender, instance: FeesReceipt, created: bool, **kwargs):
    """
    After each FeesReceipt is saved:
    1. (On Create) Generate and attach the PDF receipt.
    2. Check if the student still has an outstanding balance and
       create a Reminder if necessary.
    """
    
    # 1. Generate PDF on create
    if created:
        try:
            pdf_bytes = generate_receipt_pdf_bytes(instance.id)
            if pdf_bytes:
                # Save the PDF to the pdf_file field
                instance.pdf_file.save(
                    f"{instance.receipt_no}.pdf", 
                    ContentFile(pdf_bytes), 
                    save=True # Re-save the instance to store the file path
                )
                logger.info(f"Successfully generated PDF for receipt {instance.id}")
        except Exception as e:
            logger.error(f"Failed to auto-generate PDF for receipt {instance.id}: {e}", exc_info=True)

    # 2. Check for outstanding fees
    student = instance.student
    course = instance.course

    if not (student and course):
        # Can't check balance if student or course is not specified
        return

    # Calculate total paid for this specific course
    total_paid = (
        FeesReceipt.objects.filter(student=student, course=course)
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )
    total_due = float(course.total_fees) - float(total_paid)

    if total_due > 0:
        # Student still owes money. Check if we should send a reminder.
        last_reminder = Reminder.objects.filter(student=student, course=course).order_by("-sent_at").first()
        
        # Send reminder if one has never been sent, or if it's been >= 7 days
        if not last_reminder or (timezone.now() - last_reminder.sent_at).days >= 7:
            Reminder.objects.create(
                student=student,
                course=course,
                batch=instance.batch,
                message=f"Dear {student.user.first_name}, your outstanding fee for {course.title} is ₹{total_due:.2f}. Please pay soon.",
                status="pending",
            )
            logger.info(f"Created new fee reminder for student {student.id} for course {course.id}")