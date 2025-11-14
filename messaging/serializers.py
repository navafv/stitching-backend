"""
Serializers for the 'messaging' app.
"""

from rest_framework import serializers
from .models import Conversation, Message
from students.models import Student

class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for a single Message.
    """
    sender_name = serializers.ReadOnlyField(source="sender.get_full_name")
    # Identifies if the message is from a student or admin for UI styling
    is_from_student = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id", "conversation", "sender", "sender_name", 
            "body", "sent_at", "is_from_student"
        ]
        read_only_fields = [
            "id", "conversation", "sender", "sender_name", 
            "sent_at", "is_from_student"
        ]

    def get_is_from_student(self, obj):
        """Returns True if the sender is not a staff member."""
        return not obj.sender.is_staff

    def create(self, validated_data):
        """
        Create a new message, assigning the sender and conversation
        from the view's context.
        """
        request = self.context.get("request")
        conversation = self.context.get("conversation")
        
        if not request or not conversation:
             raise serializers.ValidationError("Serializer context is missing request or conversation.")
             
        # The model's save() method handles updating read status
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            body=validated_data['body']
        )
        return message


class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for listing conversations (Admin View).
    Provides a high-level overview of each conversation.
    """
    student_name = serializers.ReadOnlyField(source="student.user.get_full_name")
    student_reg_no = serializers.ReadOnlyField(source="student.reg_no")
    last_message_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            "id", "student", "student_name", "student_reg_no", 
            "created_at", "last_message_at", 
            "student_read", "admin_read", "last_message_preview"
        ]

    def get_last_message_preview(self, obj):
        """Returns a short preview of the most recent message."""
        last_message = obj.messages.order_by('-sent_at').first()
        if last_message:
            return (last_message.body[:50] + "...") if len(last_message.body) > 50 else last_message.body
        return None


class StudentConversationSerializer(serializers.ModelSerializer):
    """
    A specific serializer for a student viewing their *own* conversation.
    It includes all nested messages.
    """
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = [
            "id", "student", "last_message_at", 
            "student_read", "admin_read", "messages"
        ]