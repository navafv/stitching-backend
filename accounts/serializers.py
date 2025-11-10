"""
UPDATED FILE: stitching-backend/accounts/serializers.py

CRITICAL FIX: Added `is_superuser` to the UserSerializer.
This is essential for the frontend to distinguish
between an Admin (superuser) and a Teacher (staff).
"""

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import Role, User


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for the Role model."""
    class Meta:
        model = Role
        fields = ["id", "name", "description"]
        read_only_fields = ["id"]


class UserSerializer(serializers.ModelSerializer):
    """Serializer for viewing/updating users (excludes password)."""
    role = RoleSerializer(read_only=True, allow_null=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), source="role", write_only=True, required=False
    )

    student_id = serializers.ReadOnlyField(source='student.id', allow_null=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "phone", "address", "role", "role_id", "is_active", 
            "is_staff", "is_superuser", "student_id", # <-- ADDED `is_superuser`
        ]
        read_only_fields = ["id", "is_staff", "is_superuser"] # <-- ADDED `is_superuser`

    def update(self, instance, validated_data):
        """Prevent accidental password overwrite during update."""
        validated_data.pop("password", None)
        return super().update(instance, validated_data)


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users securely."""
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), source="role", write_only=True, required=False
    )
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "phone", "address", "role_id", "password",
        ]
        read_only_fields = ["id"]

    def validate_password(self, value):
        """Use Django's built-in validators."""
        validate_password(value)
        return value

    def create(self, validated_data):
        """Hashes password properly on creation."""
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user