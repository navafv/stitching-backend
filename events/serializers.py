"""
Serializers for the 'events' app.
"""

from rest_framework import serializers
from .models import Event
from django.utils import timezone

class EventSerializer(serializers.ModelSerializer):
    """
    Serializer for the Event model.
    """
    created_by_name = serializers.ReadOnlyField(source="created_by.get_full_name")
    
    class Meta:
        model = Event
        fields = [
            "id", "title", "description", "start_date", "end_date",
            "created_by", "created_by_name", "created_at"
        ]
        read_only_fields = ["id", "created_by", "created_by_name", "created_at"]

    def validate(self, attrs):
        """
        Serializer-level validation to check dates.
        """
        # On create, start_date is required
        if not self.instance and 'start_date' not in attrs:
            raise serializers.ValidationError({"start_date": "Start date is required."})

        start_date = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end_date = attrs.get('end_date', getattr(self.instance, 'end_date', None))

        # If end_date is not provided or is None, set it to start_date
        if 'end_date' not in attrs or attrs['end_date'] is None:
            attrs['end_date'] = start_date
            end_date = start_date

        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError("End date cannot be before the start date.")
        
        return attrs

    def create(self, validated_data):
        """
        Auto-assign the 'created_by' field to the
        authenticated user making the request.
        """
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)