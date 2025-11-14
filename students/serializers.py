"""
Serializers for the 'students' app.
"""

from django.db import transaction
from rest_framework import serializers
from .models import Enquiry, Student, StudentMeasurement
from accounts.serializers import UserSerializer, StudentUserCreateSerializer
from django.utils import timezone


class EnquirySerializer(serializers.ModelSerializer):
    """Serializer for managing course enquiries."""
    class Meta:
        model = Enquiry
        fields = "__all__"
        read_only_fields = ["id", "created_at"]


class StudentSerializer(serializers.ModelSerializer):
    """
    Serializer for student data.
    Handles nested User creation via the 'user_payload' field.
    """
    # Read-only nested User details
    user = UserSerializer(read_only=True)
    # Write-only field to accept data for creating a new User
    user_payload = StudentUserCreateSerializer(write_only=True, required=False)

    class Meta:
        model = Student
        fields = [
            "id", "user", "user_payload", "reg_no", "guardian_name",
            "guardian_phone", "admission_date", "address", "photo", "active",
        ]
        read_only_fields = ["id", "reg_no"]

    def validate_admission_date(self, value):
        """Ensure admission date is not in the future."""
        if value > timezone.localdate():
            raise serializers.ValidationError("Admission date cannot be in the future.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        """
        Creates a User and a Student profile together in a single transaction.
        The 'user_payload' is required for creation.
        """
        user_payload = validated_data.pop("user_payload", None)
        if not user_payload:
            raise serializers.ValidationError({
                "user_payload": "This field is required to create a new student."
            })
        
        # Create the User account
        user = StudentUserCreateSerializer().create(user_payload)
        
        # Auto-generate registration number if not provided
        if "reg_no" not in validated_data or not validated_data["reg_no"]:
             validated_data["reg_no"] = Student.generate_reg_no()
        
        # Create the Student profile linked to the user
        student = Student.objects.create(user=user, **validated_data)
        return student

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Updates the Student instance.
        'user_payload' is ignored on updates; user data must be
        updated via the /accounts/users/{id}/ endpoint.
        """
        validated_data.pop("user_payload", None)
        return super().update(instance, validated_data)


class StudentMeasurementSerializer(serializers.ModelSerializer):
    """Serializer for student measurements."""
    student_name = serializers.ReadOnlyField(source="student.user.get_full_name")

    class Meta:
        model = StudentMeasurement
        fields = "__all__"
        read_only_fields = ["id", "student"]


class StudentSelfUpdateSerializer(serializers.ModelSerializer):
    """
    A limited serializer for students to update their own profile
    via the '/students/me/' endpoint.
    Intended primarily for changing the profile photo.
    """
    class Meta:
        model = Student
        fields = ["photo"]

    
class HistoricalStudentSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for displaying student change history.
    """
    history_user_name = serializers.ReadOnlyField(source="history_user.username", allow_null=True)
    user_name = serializers.ReadOnlyField(source="user.username", allow_null=True)

    class Meta:
        model = Student.history.model
        fields = [
            "history_id",
            "history_date",
            "history_user_name",
            "history_type",
            "reg_no",
            "user_name",
            "guardian_name",
            "active",
        ]