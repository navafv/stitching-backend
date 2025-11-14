"""
Django management command to check for overdue fees.

This command can be run on a schedule (e.g., daily via cron or Celery Beat)
to find all students with outstanding balances and create Reminder objects.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from finance.models import Reminder, FeesReceipt
from courses.models import Course, Enrollment
from students.models import Student
from django.db.models import Sum
from finance.utils import send_reminder_email
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Checks for students with outstanding fees and creates/sends reminders."

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        self.stdout.write(self.style.NOTICE("Checking for overdue fees..."))
        count = 0

        # Find all active enrollments
        active_enrollments = Enrollment.objects.filter(status="active").select_related(
            "batch__course", "student__user"
        )
        
        processed_students = {} # Avoid duplicate checks for students in multiple courses

        for enrollment in active_enrollments:
            course = enrollment.batch.course
            student = enrollment.student
            
            # Create a unique key for student + course
            student_course_key = f"{student.id}-{course.id}"
            if student_course_key in processed_students:
                continue
            processed_students[student_course_key] = True

            # Calculate total paid for this specific course
            total_paid = (
                FeesReceipt.objects.filter(student=student, course=course)
                .aggregate(total=Sum("amount"))["total"]
                or 0
            )
            total_due = float(course.total_fees) - float(total_paid)

            if total_due > 0:
                # This student owes money. Check if we should send a reminder.
                last_reminder = (
                    Reminder.objects.filter(student=student, course=course)
                    .order_by("-sent_at")
                    .first()
                )
                
                # Send if no reminder exists, or if the last one was > 7 days ago
                if not last_reminder or (timezone.now() - last_reminder.sent_at).days >= 7:
                    try:
                        rem = Reminder.objects.create(
                            student=student,
                            course=course,
                            batch=enrollment.batch,
                            message=f"Dear {student.user.first_name}, your outstanding fee for {course.title} is ₹{total_due:.2f}. Please pay soon.",
                            status="pending",
                        )
                        count += 1
                        
                        # (Optional) Try to send the email immediately
                        # send_reminder_email(rem) 
                        
                    except Exception as e:
                        logger.error(f"Failed to create reminder for student {student.id}: {e}")

        self.stdout.write(self.style.SUCCESS(f"Successfully created {count} new fee reminders."))