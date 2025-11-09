"""
Finance Celery Tasks
--------------------
Handles async reminder sending and daily overdue checks.
"""

from celery import shared_task
from django.utils import timezone
from django.db.models import Sum
from .models import FeesReceipt, Reminder
from courses.models import Enrollment
from .utils import send_reminder_email


@shared_task
def send_reminder_task(reminder_id):
    """Send a reminder asynchronously."""
    from .models import Reminder  # local import to avoid circular import
    reminder = Reminder.objects.filter(id=reminder_id, status="pending").first()
    if reminder:
        send_reminder_email(reminder)
        return f"Reminder {reminder_id} sent to {reminder.student.user.email}"
    return f"Reminder {reminder_id} not found or already sent."


@shared_task
def check_overdue_fees_task():
    """Daily background task to check for overdue students."""
    from courses.models import Enrollment
    from students.models import Student

    count = 0
    for enrollment in Enrollment.objects.select_related("batch__course", "student__user"):
        course = enrollment.batch.course
        student = enrollment.student
        total_paid = (
            FeesReceipt.objects.filter(student=student, course=course)
            .aggregate(total=Sum("amount"))["total"]
            or 0
        )
        total_due = float(course.total_fees) - float(total_paid)

        if total_due > 0:
            last_reminder = (
                Reminder.objects.filter(student=student, course=course)
                .order_by("-sent_at")
                .first()
            )
            # Only send every 7 days
            if not last_reminder or (timezone.now() - last_reminder.sent_at).days >= 7:
                reminder = Reminder.objects.create(
                    student=student,
                    course=course,
                    batch=enrollment.batch,
                    message=f"Outstanding fee ₹{total_due:.2f} for {course.title}. Please pay soon.",
                    status="pending",
                )
                # Queue the async send
                send_reminder_task.delay(reminder.id)
                count += 1
    return f"{count} overdue reminders queued."
