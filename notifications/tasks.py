from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from courses.models import Batch
from finance.models import FeesReceipt
from students.models import Student
from .models import Notification

@shared_task
def generate_daily_notifications():
    today = timezone.localdate()

    # 1️⃣ Notify trainers for batches starting tomorrow
    for batch in Batch.objects.filter(start_date=today + timedelta(days=1)):
        Notification.objects.create(
            user=batch.trainer.user,
            title="Upcoming Batch Reminder",
            message=f"Your batch '{batch.code}' starts tomorrow.",
            level="info",
        )

    # 2️⃣ Notify students without any fee receipt yet
    for student in Student.objects.filter(active=True):
        if not FeesReceipt.objects.filter(student=student).exists():
            Notification.objects.create(
                user=student.user,
                title="Pending Fee Payment",
                message="You haven’t made your first fee payment yet.",
                level="warning",
            )
