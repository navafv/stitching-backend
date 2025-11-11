from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Certificate
from .utils import generate_certificate_pdf_sync  # <-- MODIFIED import

@receiver(post_save, sender=Certificate)
def auto_generate_pdf(sender, instance, created, **kwargs):
    """Generate PDF after issuing new certificate."""
    if created:
        # This is now a SYNCHRONOUS call.
        # The API request will wait until this is finished.
        generate_certificate_pdf_sync(instance.id)