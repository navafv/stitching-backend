"""
Django management command to generate daily notifications.

This is an example of how to create system-generated notifications
that can be run on a schedule (e..g, via Celery Beat or cron).
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from finance.models import FeesReceipt
from students.models import Student
from notifications.models import Notification
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Generates daily notifications for students (e.g., pending fees)."

    def handle(self, *args, **kwargs):
        today = timezone.localdate()
        self.stdout.write(self.style.NOTICE("Generating daily notifications..."))
        
        count = 0

        # 1. Example: Notify active students who have not made any payment
        active_students = Student.objects.filter(
            active=True,
            user__is_active=True
        ).prefetch_related('receipts')

        for student in active_students:
            if not student.receipts.exists():
                # get_or_create prevents duplicate notifications
                obj, created = Notification.objects.get_or_create(
                    user=student.user,
                    title="Pending Fee Payment",
                    defaults={
                        "message": "You have not made your first fee payment. Please contact the admin.",
                        "level": "warning",
                    }
                )
                if created:
                    count += 1
        
        # (Future examples: notify about upcoming batch starts, etc.)
        
        self.stdout.write(self.style.SUCCESS(
            f"Successfully created or found {count} new notifications."
        ))