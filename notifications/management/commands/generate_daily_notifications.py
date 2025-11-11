from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from courses.models import Batch
from finance.models import FeesReceipt
from students.models import Student
from notifications.models import Notification

class Command(BaseCommand):
    help = "Generates daily notifications for upcoming batches and pending fees."

    def handle(self, *args, **kwargs):
        today = timezone.localdate()
        self.stdout.write("Generating daily notifications...")
        
        count = 0

        # 1. Notify trainers for batches starting tomorrow
        for batch in Batch.objects.filter(start_date=today + timedelta(days=1)):
            if batch.trainer: # Check if trainer exists
                Notification.objects.get_or_create(
                    user=batch.trainer.user,
                    title="Upcoming Batch Reminder",
                    message=f"Your batch '{batch.code}' starts tomorrow.",
                    level="info",
                )
                count += 1

        # 2. Notify students without any fee receipt yet
        for student in Student.objects.filter(active=True, user__is_active=True):
            if not FeesReceipt.objects.filter(student=student).exists():
                Notification.objects.get_or_create(
                    user=student.user,
                    title="Pending Fee Payment",
                    message="You haven’t made your first fee payment yet.",
                    level="warning",
                )
                count += 1
        
        self.stdout.write(self.style.SUCCESS(f"Successfully created or found {count} new notifications."))