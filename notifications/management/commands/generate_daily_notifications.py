from django.core.management.base import BaseCommand
from django.utils import timezone
from finance.models import FeesReceipt
from students.models import Student
from notifications.models import Notification

class Command(BaseCommand):
    help = "Generates daily notifications for upcoming batches and pending fees."

    def handle(self, *args, **kwargs):
        today = timezone.localdate()
        self.stdout.write("Generating daily notifications...")
        
        count = 0

        # 1. Notify students without any fee receipt yet
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