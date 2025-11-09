"""
Daily fee check command.
------------------------
Finds all overdue students and creates new reminders automatically.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from finance.models import Reminder, FeesReceipt
from courses.models import Course, Enrollment
from students.models import Student
from django.db.models import Sum
from finance.utils import send_reminder_email


class Command(BaseCommand):
    help = "Checks for students with outstanding fees and creates reminders."

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
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
                if not last_reminder or (timezone.now() - last_reminder.sent_at).days >= 7:
                    rem = Reminder.objects.create(
                        student=student,
                        course=course,
                        batch=enrollment.batch,
                        message=f"Outstanding fee ₹{total_due:.2f} for {course.title}. Please pay soon.",
                        status="pending",
                    )
                    count += 1
                    send_reminder_email(rem)

        self.stdout.write(self.style.SUCCESS(f"{count} overdue reminders created."))
