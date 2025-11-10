"""
Courses Serializers
-------------------
Enhancements:
- Added validation and nested display fields.
- Added atomic enrollment creation with capacity checks.
- Added 'has_feedback' field to EnrollmentSerializer.
"""

from django.db import transaction
from rest_framework import serializers
from .models import Course, Trainer, Batch, Enrollment, BatchFeedback


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
    course_title = serializers.ReadOnlyField(source="batch.course.title")
    has_feedback = serializers.SerializerMethodField()
    course_id = serializers.ReadOnlyField(source="batch.course.id") # <-- **ADD THIS LINE**

    class Meta:
        model = Enrollment
        fields = [
            "id", "student", "student_name", "batch", "batch_code", 
            "enrolled_on", "status", "course_title", "has_feedback",
            "course_id"  # <-- **ADD THIS FIELD**
        ]
        read_only_fields = ["id", "enrolled_on"]

    def get_has_feedback(self, obj):
        # Check if the one-to-one reverse relation exists
        return hasattr(obj, 'feedback')

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


class BatchFeedbackSerializer(serializers.ModelSerializer):
    student_name = serializers.ReadOnlyField(source="enrollment.student.user.get_full_name")
    batch_code = serializers.ReadOnlyField(source="enrollment.batch.code")

    class Meta:
        model = BatchFeedback
        fields = [
            "id", "enrollment", "student_name", "batch_code", 
            "rating", "comments", "submitted_at"
        ]
        read_only_fields = ["id", "submitted_at"]

    def validate_enrollment(self, enrollment):
        """
        Check if the feedback is from the currently logged-in user.
        """
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required.")
        
        if enrollment.student.user != request.user:
            raise serializers.ValidationError("You can only submit feedback for your own enrollments.")
        
        if enrollment.status != "completed":
            # Optional: only allow feedback on completed courses
            raise serializers.ValidationError("Feedback can only be submitted for completed batches.")
            
        if BatchFeedback.objects.filter(enrollment=enrollment).exists():
            raise serializers.ValidationError("Feedback has already been submitted for this enrollment.")
            
        return enrollment