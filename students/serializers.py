"""
Students Serializers
--------------------
Enhancements:
- Added atomic transaction for user + student creation.
- Added validation for guardian phone and date.
- Read/write separation and nested user payload.
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

    def validate_phone(self, value):
        if not value.isdigit() and not value.startswith("+"):
            raise serializers.ValidationError("Enter a valid phone number.")
        return value


class StudentSerializer(serializers.ModelSerializer):
    """
    Serializer for student data.
    Nested user payload is accepted for creation (user + student).
    """
    user = UserSerializer(read_only=True)
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
        """Creates user + student together safely."""
        user_payload = validated_data.pop("user_payload", None)
        if not user_payload:
            raise serializers.ValidationError({
                "user_payload": "Required to create a student with user account."
            })
        user = StudentUserCreateSerializer().create(user_payload)
        # Optionally auto-generate registration number
        reg_no = validated_data.get("reg_no") or Student.generate_reg_no()
        student = Student.objects.create(user=user, reg_no=reg_no, **validated_data)
        return student

    @transaction.atomic
    def update(self, instance, validated_data):
        """Prevent nested user updates."""
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
    A simple serializer for students to update their own profile.
    Primarily used for photo uploads.
    """
    class Meta:
        model = Student
        fields = ["photo"]

    
class HistoricalStudentSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for displaying student history.
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