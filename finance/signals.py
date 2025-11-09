"""
Finance Signals
---------------
Triggers fee reminders when overdue conditions are met.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import FeesReceipt, Reminder
from courses.models import Enrollment
from students.models import Student
from django.db.models import Sum


@receiver(post_save, sender=FeesReceipt)
def check_overdue_after_payment(sender, instance, created, **kwargs):
    """
    After each receipt is saved, check if the student still owes money.
    If overdue, schedule or create a reminder.
    """
    student = instance.student
    course = instance.course

    # Calculate total paid and expected
    total_paid = (
        FeesReceipt.objects.filter(student=student, course=course)
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )
    total_due = float(course.total_fees) - float(total_paid)

    # If still owes more than 0 and not recently reminded
    if total_due > 0:
        last_reminder = Reminder.objects.filter(student=student, course=course).order_by("-sent_at").first()
        if not last_reminder or (timezone.now() - last_reminder.sent_at).days >= 7:
            Reminder.objects.create(
                student=student,
                course=course,
                batch=instance.batch,
                message=f"Dear {student.user.first_name}, your outstanding fee for {course.title} is ₹{total_due:.2f}. Please pay soon.",
                status="pending",
            )
