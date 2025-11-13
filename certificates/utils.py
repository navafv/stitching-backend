from django.template.loader import render_to_string
from django.core.files.base import ContentFile
# --- 1. REMOVE WEASYPRINT, IMPORT XHTML2PDF ---
# from weasyprint import HTML
from xhtml2pdf import pisa
# --- END IMPORTS ---
import io
import logging
from .models import Certificate
from django.conf import settings 

logger = logging.getLogger(__name__)

# --- 2. RENAME FUNCTION TO BE CLEAR ---
def generate_certificate_pdf_sync(cert_id):
    """
    Generates a PDF certificate SYNCHRONOUSLY using xhtml2pdf.
    """
    cert = Certificate.objects.select_related("student__user", "course").filter(id=cert_id).first()
    if not cert:
        logger.warning(f"Certificate {cert_id} not found for PDF generation.")
        return

    try:
        # --- Build the verification URL ---
        frontend_url = settings.CORS_ALLOWED_ORIGINS[0] 
        verify_url = f"{frontend_url}/verify?hash={cert.qr_hash}"
        
        # --- Logic to convert weeks to months ---
        duration_text = ""
        if cert.course and cert.course.duration_weeks:
            if cert.course.duration_weeks == 12:
                duration_text = "3 Month"
            elif cert.course.duration_weeks == 24:
                duration_text = "6 Month"
            else:
                duration_text = f"{cert.course.duration_weeks} Week"

        context = {
            "certificate": cert,
            "verify_url": verify_url,
            "duration_text": duration_text
        }
        
        # Prepare HTML content
        html_content = render_to_string("certificates/template.html", context)
        
        # Use in-memory BytesIO
        pdf_buffer = io.BytesIO()
        
        # --- 3. Use pisa to create the PDF ---
        pisa_status = pisa.CreatePDF(
            html_content,    # the HTML to convert
            dest=pdf_buffer  # file-like object to receive result
        )

        if pisa_status.err:
            logger.error(f"Error generating PDF for {cert.certificate_no}: {pisa_status.err}")
            return
        # --- END PDF CREATION ---
        
        pdf_buffer.seek(0)
        
        # Save the buffer's contents directly to the model's FileField
        cert.pdf_file.save(f"{cert.certificate_no}.pdf", ContentFile(pdf_buffer.read()), save=True)
        logger.info(f"Successfully generated PDF for {cert.certificate_no}")
    
    except Exception as e:
        logger.error(f"Error generating PDF for {cert.certificate_no}: {e}", exc_info=True)