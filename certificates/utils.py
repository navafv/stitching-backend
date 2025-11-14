"""
Utility functions for the 'certificates' app, primarily for PDF generation.
"""

from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from xhtml2pdf import pisa  # PDF generation library
import io
import logging
from .models import Certificate
from django.conf import settings 

logger = logging.getLogger(__name__)

def generate_certificate_pdf_sync(cert_id: int):
    """
    Generates a PDF for a specific Certificate instance and saves it
    to the model's `pdf_file` field. Runs synchronously.
    
    This is called by a post_save signal.
    """
    try:
        cert = Certificate.objects.select_related("student__user", "course").get(id=cert_id)
    except Certificate.DoesNotExist:
        logger.warning(f"Certificate {cert_id} not found for PDF generation.")
        return
    
    # Do not re-generate if a file already exists
    if cert.pdf_file:
        logger.info(f"PDF for {cert.certificate_no} already exists. Skipping generation.")
        return

    try:
        # Assume the first allowed origin is the frontend URL for verification
        frontend_url = settings.CORS_ALLOWED_ORIGINS[0] 
        verify_url = f"{frontend_url}/verify?hash={cert.qr_hash}"
        
        # Simple logic to convert course duration (in weeks) to text
        duration_text = ""
        if cert.course and cert.course.duration_weeks:
            weeks = cert.course.duration_weeks
            if weeks == 12: # 3 months
                duration_text = "3 Month"
            elif weeks == 24: # 6 months
                duration_text = "6 Month"
            else:
                duration_text = f"{weeks} Week"

        context = {
            "certificate": cert,
            "verify_url": verify_url,
            "duration_text": duration_text
        }
        
        # Render the HTML template
        html_content = render_to_string("certificates/template.html", context)
        
        pdf_buffer = io.BytesIO()
        
        # Generate the PDF
        pisa_status = pisa.CreatePDF(
            html_content,
            dest=pdf_buffer
        )

        if pisa_status.err:
            logger.error(f"Error generating PDF for {cert.certificate_no}: {pisa_status.err}")
            return
        
        pdf_buffer.seek(0)
        file_name = f"{cert.certificate_no}.pdf"
        
        # Save the generated PDF to the FileField
        # This triggers a *second* save, but signals are configured
        # to only run on `created=True`, so it won't loop.
        cert.pdf_file.save(file_name, ContentFile(pdf_buffer.read()), save=True)
        logger.info(f"Successfully generated and saved PDF for {cert.certificate_no}")
    
    except Exception as e:
        logger.error(f"Unhandled error generating PDF for {cert.certificate_no}: {e}", exc_info=True)