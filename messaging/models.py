"""
Data models for the 'messaging' app.

Defines:
- Conversation: A 1-to-1 thread between a Student and the Admin team.
- Message: A single message within a Conversation.
"""

from django.db import models
from django.conf import settings
from students.models import Student

class Conversation(models.Model):
    """
    Represents a single messaging thread between one student
    and the admin team.
    """
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name="conversation")
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(auto_now=True)
    
    # Tracks read status for both parties
    student_read = models.BooleanField(default=True)
    admin_read = models.BooleanField(default=True)

    class Meta:
        ordering = ["-last_message_at"]
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"

    def __str__(self):
        return f"Conversation with {self.student.user.get_full_name()}"

    def mark_as_read_by(self, user):
        """
        Marks the conversation as read by the user (student or admin)
        who is currently viewing it.
        """
        if not user.is_staff: # User is the student
            self.student_read = True
        else: # User is an admin
            self.admin_read = True
        self.save(update_fields=["student_read", "admin_read"])

    def mark_as_unread_for(self, sender_type: str):
        """
        Marks the conversation as unread for the *recipient*.
        Called by the Message.save() signal.
        
        Args:
            sender_type: 'student' or 'admin'
        """
        if sender_type == 'student': # Message sent by student
            self.admin_read = False
            self.save(update_fields=["admin_read"])
        else: # Message sent by admin
            self.student_read = False
            self.save(update_fields=["student_read"])


class Message(models.Model):
    """
    Represents a single message within a conversation.
    """
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages")
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sent_at"] # Oldest first, for chat history
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"Message from {self.sender.username} at {self.sent_at.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        """
        On save, update the conversation's unread status for the recipient.
        The 'last_message_at' timestamp on the Conversation model is
        updated automatically via its 'auto_now=True' setting.
        """
        # Determine who the sender is to set unread status for the *other* party
        sender_type = 'student' if not self.sender.is_staff else 'admin'
        self.conversation.mark_as_unread_for(sender_type)
        
        super().save(*args, **kwargs)