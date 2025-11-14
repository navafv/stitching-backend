"""
Serializers for the 'notifications' app.
"""

from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Notification model.
    Used for listing, retrieving, and updating (e.g., marking as read).
    """
    class Meta:
        model = Notification
        fields = "__all__"
        # User is set automatically based on authentication
        read_only_fields = ["id", "created_at", "user"]


class NotificationCreateSerializer(serializers.Serializer):
    """
    A non-model serializer used *only* to validate the payload
    for the 'send-bulk' admin action.
    """
    title = serializers.CharField(max_length=120, required=True)
    message = serializers.CharField(required=True)
    level = serializers.ChoiceField(
        choices=Notification.LEVEL_CHOICES,
        default="info"
    )
    
    # Target audience fields (at least one is required)
    user_id = serializers.IntegerField(required=False, allow_null=True)
    role_id = serializers.IntegerField(required=False, allow_null=True)
    send_to_all = serializers.BooleanField(required=False, default=False)

    def validate(self, data):
        """Ensure at least one target audience is specified."""
        if not data.get("user_id") and not data.get("role_id") and not data.get("send_to_all"):
            raise serializers.ValidationError(
                "Must provide at least one target: user_id, role_id, or send_to_all."
            )
        return data