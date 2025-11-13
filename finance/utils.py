from django.template.loader import render_to_string
# --- 1. REMOVE WEASYPRINT, IMPORT XHTML2PDF ---
# from weasyprint import HTML
from xhtml2pdf import pisa
from django.core.files.base import ContentFile
# --- END IMPORTS ---

import io
import logging
from .models import Reminder, FeesReceipt
from django.conf import settings

logger = logging.getLogger(__name__)

def send_reminder_email(reminder: Reminder):
    # ... (this function is unchanged)
    student_email = reminder.student.user.email
    if not student_email:
        reminder.status = "failed"
        reminder.save()
        return False

    try:
        send_mail(
            subject="Fee Reminder - Stitching Institute",
            message=reminder.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student_email],
            fail_silently=True,
        )
        reminder.status = "sent"
        reminder.save()
        return True
    except Exception:
        reminder.status = "failed"
        reminder.save()
        return False


# --- 2. UPDATE THIS FUNCTION TO USE XHTML2PDF ---
def generate_receipt_pdf_bytes(receipt_id: int) -> bytes:
    """
    Generates a PDF for a FeesReceipt and returns it as raw bytes.
    """
    receipt = FeesReceipt.objects.select_related(
        "student__user", "course"
    ).filter(id=receipt_id).first()
    
    if not receipt:
        logger.warning(f"Receipt {receipt_id} not found for PDF generation.")
        return None

    try:
        context = {"receipt": receipt}
        
        # Render the HTML template
        html_content = render_to_string("finance/receipt_template.html", context)
        
        # Use in-memory BytesIO buffer
        pdf_buffer = io.BytesIO()
        
        # --- 3. Use pisa to create the PDF ---
        pisa_status = pisa.CreatePDF(
            html_content,    # the HTML to convert
            dest=pdf_buffer  # file-like object to receive result
        )

        if pisa_status.err:
            logger.error(f"Error generating PDF for {receipt.receipt_no}: {pisa_status.err}")
            return None
        # --- END PDF CREATION ---
        
        # Get the bytes from the buffer
        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()
        
        logger.info(f"Successfully generated PDF bytes for {receipt.receipt_no}")
        return pdf_bytes
    
    except Exception as e:
        logger.error(f"Error generating PDF for {receipt.receipt_no}: {e}", exc_info=True)
        return None