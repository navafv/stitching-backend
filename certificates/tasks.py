from celery import shared_task
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from weasyprint import HTML
import tempfile
from .models import Certificate


@shared_task
def generate_certificate_pdf(cert_id):
    """Generates a PDF certificate asynchronously."""
    cert = Certificate.objects.select_related("student__user", "course").filter(id=cert_id).first()
    if not cert:
        return "Certificate not found."

    # Prepare HTML content
    html_content = render_to_string("certificates/template.html", {"certificate": cert})
    with tempfile.NamedTemporaryFile(suffix=".pdf") as pdf_file:
        HTML(string=html_content).write_pdf(pdf_file.name)
        pdf_file.seek(0)
        cert.pdf_file.save(f"{cert.certificate_no}.pdf", ContentFile(pdf_file.read()), save=True)

    return f"PDF generated for {cert.certificate_no}"
