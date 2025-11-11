from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from weasyprint import HTML
import io
import logging
from .models import Certificate
from django.conf import settings # <-- Import settings

# Set up a logger
logger = logging.getLogger(__name__)

def generate_certificate_pdf_sync(cert_id):
    """
    Generates a PDF certificate SYNCHRONOUSLY.
    """
    cert = Certificate.objects.select_related("student__user", "course").filter(id=cert_id).first()
    if not cert:
        logger.warning(f"Certificate {cert_id} not found for PDF generation.")
        return

    try:
        # --- Build the verification URL ---
        frontend_url = settings.CORS_ALLOWED_ORIGINS[0] 
        verify_url = f"{frontend_url}/verify?hash={cert.qr_hash}"
        
        # --- NEW: Logic to convert weeks to months ---
        duration_text = ""
        if cert.course and cert.course.duration_weeks:
            if cert.course.duration_weeks == 12:
                duration_text = "3 Month"
            elif cert.course.duration_weeks == 24:
                duration_text = "6 Month"
            else:
                # Fallback for any other duration
                duration_text = f"{cert.course.duration_weeks} Week"
        # --- END NEW LOGIC ---

        context = {
            "certificate": cert,
            "verify_url": verify_url,
            "duration_text": duration_text  # <-- Pass new variable to template
        }
        
        # Prepare HTML content
        html_content = render_to_string("certificates/template.html", context)
        
        # Use in-memory BytesIO
        pdf_buffer = io.BytesIO()
        
        # Write the PDF directly to the in-memory buffer
        HTML(string=html_content).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)
        
        # Save the buffer's contents directly to the model's FileField
        cert.pdf_file.save(f"{cert.certificate_no}.pdf", ContentFile(pdf_buffer.read()), save=True)
        logger.info(f"Successfully generated PDF for {cert.certificate_no}")
    
    except Exception as e:
        # Log the error if something goes wrong
        logger.error(f"Error generating PDF for {cert.certificate_no}: {e}", exc_info=True)