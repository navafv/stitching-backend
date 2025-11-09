"""
Courses Serializers
-------------------
Enhancements:
- Added validation and nested display fields.
- Added atomic enrollment creation with capacity checks.
"""

from django.db import transaction
from rest_framework import serializers
from .models import Course, Trainer, Batch, Enrollment


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Course model."""
    class Meta:
        model = Course
        fields = "__all__"


class TrainerSerializer(serializers.ModelSerializer):
    """Serializer for Trainer model."""
    trainer_name = serializers.ReadOnlyField(source="user.get_full_name")

    class Meta:
        model = Trainer
        fields = ["id", "user", "trainer_name", "emp_no", "join_date", "salary", "is_active"]


class BatchSerializer(serializers.ModelSerializer):
    """Serializer for Batch model."""
    course_title = serializers.ReadOnlyField(source="course.title")
    trainer_name = serializers.ReadOnlyField(source="trainer.user.get_full_name")

    class Meta:
        model = Batch
        fields = [
            "id", "course", "course_title", "trainer", "trainer_name",
            "code", "start_date", "end_date", "capacity", "schedule",
        ]

    def validate(self, data):
        """Ensure valid date range for batches."""
        start_date, end_date = data.get("start_date"), data.get("end_date")
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError("End date cannot be before start date.")
        return data


class EnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for Enrollment model with validation."""
    student_name = serializers.ReadOnlyField(source="student.user.get_full_name")
    batch_code = serializers.ReadOnlyField(source="batch.code")

    class Meta:
        model = Enrollment
        fields = ["id", "student", "student_name", "batch", "batch_code", "enrolled_on", "status"]
        read_only_fields = ["id", "enrolled_on"]

    @transaction.atomic
    def create(self, validated_data):
        """Prevent enrolling student into full or duplicate batch."""
        batch = validated_data["batch"]
        student = validated_data["student"]

        # Capacity check
        if batch.is_full():
            raise serializers.ValidationError("Batch capacity reached.")

        # Duplicate check
        if Enrollment.objects.filter(student=student, batch=batch).exists():
            raise serializers.ValidationError("Student already enrolled in this batch.")

        return super().create(validated_data)
