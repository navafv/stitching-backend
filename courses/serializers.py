"""
Serializers for the 'courses' app.

Handles validation and data transformation for Course, Trainer, Batch,
Enrollment, Feedback, and CourseMaterial models.
"""

from django.db import transaction
from rest_framework import serializers
from .models import Course, Trainer, Batch, Enrollment, BatchFeedback, CourseMaterial


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Course model."""
    class Meta:
        model = Course
        fields = [
            "id", "code", "title", "duration_weeks", "total_fees", 
            "syllabus", "active", "required_attendance_days"
        ]


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
            "code", "capacity", "schedule",
        ]


class EnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Enrollment model.
    Includes business logic for validation and computed fields.
    """
    student_name = serializers.ReadOnlyField(source="student.user.get_full_name")
    batch_code = serializers.ReadOnlyField(source="batch.code")
    course_title = serializers.ReadOnlyField(source="batch.course.title")
    course_id = serializers.ReadOnlyField(source="batch.course.id")
    completion_date = serializers.DateField(read_only=True)
    
    # Check if student has already submitted feedback
    has_feedback = serializers.SerializerMethodField()
    
    # Compute attendance progress
    present_days = serializers.SerializerMethodField()
    required_days = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            "id", "student", "student_name", "batch", "batch_code", 
            "enrolled_on", "status", "course_title", "has_feedback",
            "course_id", "completion_date",
            "present_days", "required_days"
        ]
        read_only_fields = ["id", "enrolled_on"]
    
    def get_present_days(self, obj):
        """Returns the student's total present days for this course."""
        return obj.get_present_days_count()

    def get_required_days(self, obj):
        """Returns the course's attendance requirement."""
        return obj.batch.course.required_attendance_days

    def get_has_feedback(self, obj):
        """Checks if a related BatchFeedback object exists."""
        return hasattr(obj, 'feedback')

    @transaction.atomic
    def create(self, validated_data):
        """
        Validates enrollment creation.
        1. Prevents enrolling in a full batch.
        2. Prevents duplicate enrollment in the same batch.
        """
        batch = validated_data["batch"]
        student = validated_data["student"]

        # 1. Capacity check
        if batch.is_full():
            raise serializers.ValidationError("Batch capacity reached.")

        # 2. Duplicate check
        if Enrollment.objects.filter(student=student, batch=batch).exists():
            raise serializers.ValidationError("Student already enrolled in this batch.")

        return super().create(validated_data)


class BatchFeedbackSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and viewing BatchFeedback.
    """
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
        Validates feedback submission.
        1. Ensures the user submitting is the student on the enrollment.
        2. (Optional) Ensures the course is 'completed'.
        3. Ensures feedback hasn't already been submitted.
        """
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required.")
        
        # 1. Check ownership
        if enrollment.student.user != request.user:
            raise serializers.ValidationError("You can only submit feedback for your own enrollments.")
        
        # 2. Check if course is completed
        if enrollment.status != "completed":
            # This is an optional business rule.
            raise serializers.ValidationError("Feedback can only be submitted for completed batches.")
            
        # 3. Check for duplicates
        if BatchFeedback.objects.filter(enrollment=enrollment).exists():
            raise serializers.ValidationError("Feedback has already been submitted for this enrollment.")
            
        return enrollment


class CourseMaterialSerializer(serializers.ModelSerializer):
    """
    Serializer for uploading and viewing course materials.
    Handles 'file' vs 'link' validation.
    """
    course_title = serializers.ReadOnlyField(source="course.title")

    class Meta:
        model = CourseMaterial
        fields = [
            "id", "course_title", "title", "description",
            "file", "link", "uploaded_at"
        ]
        read_only_fields = ["id", "uploaded_at", "course_title"]

    def validate(self, attrs):
        """
        Ensures either 'file' or 'link' is provided, but not both.
        """
        # Get the final state of file/link fields
        file = attrs.get("file", getattr(self.instance, 'file', None))
        link = attrs.get("link", getattr(self.instance, 'link', None))
        
        # Handle exclusive-or logic
        if not file and not link:
            raise serializers.ValidationError("Must provide either a file or a link.")
        if file and link:
            raise serializers.ValidationError("Cannot provide both a file and a link.")

        return attrs

    def create(self, validated_data):
        """
        Automatically assigns the 'course' from the nested URL
        (e.g., /courses/<course_pk>/materials/).
        """
        course_pk = self.context['view'].kwargs.get('course_pk')
        if not course_pk:
            raise serializers.ValidationError("Course ID not found in URL context.")
            
        validated_data['course_id'] = course_pk
        return super().create(validated_data)