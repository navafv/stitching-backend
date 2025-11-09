from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Certificate
from .tasks import generate_certificate_pdf

@receiver(post_save, sender=Certificate)
def auto_generate_pdf(sender, instance, created, **kwargs):
    """Generate PDF after issuing new certificate."""
    if created:
        generate_certificate_pdf.delay(instance.id)
