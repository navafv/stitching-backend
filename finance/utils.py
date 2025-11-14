"""
Utility functions for the 'finance' app.
Includes PDF generation and email sending logic.
"""

from django.template.loader import render_to_string
from xhtml2pdf import pisa # PDF generation library
from django.core.files.base import ContentFile
from django.core.mail import send_mail
import io
import logging
from .models import Reminder, FeesReceipt
from django.conf import settings

logger = logging.getLogger(__name__)

def send_reminder_email(reminder: Reminder):
    """
    (Not currently used by a signal, but available)
    Sends a fee reminder email to a student.
    """
    student_email = reminder.student.user.email
    if not student_email:
        reminder.status = "failed"
        reminder.save()
        logger.warning(f"Failed to send reminder {reminder.id}: Student {reminder.student.id} has no email.")
        return False

    try:
        send_mail(
            subject="Fee Reminder - Noor Stitching Institute",
            message=reminder.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student_email],
            fail_silently=False, # Fail loudly to catch errors
        )
        reminder.status = "sent"
        reminder.save()
        logger.info(f"Sent reminder email for reminder {reminder.id} to {student_email}")
        return True
    except Exception as e:
        reminder.status = "failed"
        reminder.save()
        logger.error(f"Error sending reminder email for {reminder.id}: {e}", exc_info=True)
        return False


def generate_receipt_pdf_bytes(receipt_id: int) -> bytes | None:
    """
    Generates a PDF for a specific FeesReceipt using a template
    and returns it as raw bytes.
    """
    try:
        receipt = FeesReceipt.objects.select_related(
            "student__user", "course"
        ).get(id=receipt_id)
    except FeesReceipt.DoesNotExist:
        logger.warning(f"Receipt {receipt_id} not found for PDF generation.")
        return None

    try:
        context = {"receipt": receipt}
        
        # Render the HTML template to a string
        html_content = render_to_string("finance/receipt_template.html", context)
        
        # Create an in-memory BytesIO buffer
        pdf_buffer = io.BytesIO()
        
        # Use pisa to create the PDF from HTML
        pisa_status = pisa.CreatePDF(
            html_content,    # the HTML to convert
            dest=pdf_buffer  # file-like object to receive result
        )

        if pisa_status.err:
            logger.error(f"Error generating PDF for {receipt.receipt_no}: {pisa_status.err}")
            return None
        
        # Get the bytes from the buffer
        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()
        
        logger.info(f"Successfully generated PDF bytes for {receipt.receipt_no}")
        return pdf_bytes
    
    except Exception as e:
        logger.error(f"Error in generate_receipt_pdf_bytes for {receipt.receipt_no}: {e}", exc_info=True)
        return None