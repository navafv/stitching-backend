from django.core.mail import send_mail
from django.conf import settings
from .models import Reminder

def send_reminder_email(reminder: Reminder):
    """Sends email and updates status."""
    student_email = reminder.student.user.email
    if not student_email:
        reminder.status = "failed"
        reminder.save()
        return False

    try:
        send_mail(
            subject="Fee Reminder - Stitching Institute",
            message=reminder.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student_email],
            fail_silently=True,
        )
        reminder.status = "sent"
        reminder.save()
        return True
    except Exception:
        reminder.status = "failed"
        reminder.save()
        return False
