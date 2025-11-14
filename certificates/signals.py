"""
Signal handlers for the 'certificates' app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Certificate
from .utils import generate_certificate_pdf_sync
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Certificate)
def auto_generate_pdf_on_create(sender, instance, created, **kwargs):
    """
    When a new Certificate is created, synchronously generate
    and attach its PDF file.
    """
    if created:
        try:
            # This is a synchronous call. The API request will wait
            # for the PDF to be generated and saved.
            generate_certificate_pdf_sync(instance.id)
        except Exception as e:
            logger.error(f"Failed to auto-generate PDF for certificate {instance.id}: {e}", exc_info=True)