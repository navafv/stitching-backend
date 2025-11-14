"""
Admin configuration for the 'messaging' app.
"""

from django.contrib import admin
from .models import Conversation, Message

class MessageInline(admin.TabularInline):
    """
    Read-only inline view of messages within a Conversation
    in the admin panel.
    """
    model = Message
    extra = 0
    readonly_fields = ("sender", "body", "sent_at")
    can_delete = False
    ordering = ("sent_at",)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("student", "last_message_at", "student_read", "admin_read")
    list_filter = ("student_read", "admin_read")
    search_fields = ("student__user__first_name", "student__user__last_name")
    readonly_fields = ("student", "created_at", "last_message_at")
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Separate admin view for Messages (primarily for debugging/viewing).
    Messages should ideally be managed via the Conversation inline.
    """
    list_display = ("conversation", "sender", "sent_at", "body_preview")
    search_fields = ("body", "sender__username")
    readonly_fields = ("conversation", "sender", "sent_at", "body")
    autocomplete_fields = ['conversation', 'sender']

    @admin.display(description="Message")
    def body_preview(self, obj):
        """Shortens the message body for the list display."""
        return (obj.body[:75] + "...") if len(obj.body) > 75 else obj.body