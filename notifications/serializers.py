from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"
        read_only_fields = ["id", "created_at", "user"]


class NotificationCreateSerializer(serializers.Serializer):
    """
    Serializer to validate data for sending a bulk notification.
    Not tied to a model.
    """
    title = serializers.CharField(max_length=120)
    message = serializers.CharField()
    level = serializers.ChoiceField(choices=["info", "warning", "success", "error"], default="info")
    
    # Target audience
    user_id = serializers.IntegerField(required=False, allow_null=True)
    role_id = serializers.IntegerField(required=False, allow_null=True)
    send_to_all = serializers.BooleanField(required=False, default=False)

    def validate(self, data):
        """Ensure at least one target audience is specified."""
        if not data.get("user_id") and not data.get("role_id") and not data.get("send_to_all"):
            raise serializers.ValidationError("Must provide one of: user_id, role_id, or send_to_all.")
        return data