"""
Serializers for the 'accounts' app.

Handles the conversion of User and Role models to and from JSON,
including logic for user creation, password changes, and password resets.
"""

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import Role, User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for the Role model."""
    class Meta:
        model = Role
        fields = ["id", "name", "description"]
        read_only_fields = ["id"]


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing and updating User instances.
    Excludes password fields for security.
    """
    # Read-only nested representation of the role
    role = RoleSerializer(read_only=True, allow_null=True)
    # Write-only field to update the role by its ID
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), source="role", write_only=True, required=False, allow_null=True
    )
    # Read-only field to show the associated student ID, if one exists
    student_id = serializers.ReadOnlyField(source='student.id', allow_null=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "phone", "address", "role", "role_id", "is_active", 
            "is_staff", "is_superuser", "student_id",
        ]
        # Password is not included for reads/updates
        # is_superuser is set at the DB level, not via API
        read_only_fields = ["id", "is_superuser", "student_id"] 


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users (Admin use).
    Handles password hashing and allows setting staff status.
    """
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), source="role", write_only=True, required=False, allow_null=True
    )
    password = serializers.CharField(write_only=True, validators=[validate_password])
    is_staff = serializers.BooleanField(default=False, required=False)

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "phone", "address", "role_id", "password", "is_staff",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        """Creates a new user instance with a hashed password."""
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class StudentUserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new user tied to a Student profile.
    This is used by the StudentSerializer to create a User and Student
    in one step. It ensures 'is_staff' and 'is_superuser' are always False.
    """
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), source="role", write_only=True, required=False, allow_null=True
    )
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "phone", "address", "role_id", "password",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        """Creates a new non-staff user with a hashed password."""
        password = validated_data.pop("password")
        
        # Ensure student accounts are never created as staff or superusers
        validated_data['is_staff'] = False
        validated_data['is_superuser'] = False
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
    

class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for an authenticated user to change their own password.
    Requires the user's current password for validation.
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])

    def validate_old_password(self, value):
        """Check that the old password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Wrong password.")
        return value

    def save(self, **kwargs):
        """Sets the new password for the user."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
    

class HistoricalUserSerializer(serializers.ModelSerializer):
    """Read-only serializer for displaying User change history."""
    history_user_name = serializers.ReadOnlyField(source="history_user.username", allow_null=True)
    
    class Meta:
        model = User.history.model
        fields = [
            "history_id",
            "history_date",
            "history_user_name",
            "history_type",
            "history_change_reason",
            "username",
            "first_name",
            "last_name",
            "is_staff",
            "is_active",
        ]


class PasswordResetRequestSerializer(serializers.Serializer):
    """Validates the email for a password reset request."""
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Ensure an active user exists with the provided email."""
        if not User.objects.filter(email__iexact=value, is_active=True).exists():
            raise serializers.ValidationError("No active user found with this email address.")
        return value


class SetNewPasswordSerializer(serializers.Serializer):
    """
    Validates the token and new password for setting a new password.
    """
    uidb64 = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])

    def validate(self, attrs):
        """Validate the UID and token."""
        try:
            uid = force_str(urlsafe_base64_decode(attrs.get('uidb64')))
            self.user = UserModel.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
            raise serializers.ValidationError("Invalid reset link.")

        if not PasswordResetTokenGenerator().check_token(self.user, attrs.get('token')):
            raise serializers.ValidationError("Invalid or expired reset link.")

        return attrs

    def save(self, **kwargs):
        """Sets the new password for the validated user."""
        self.user.set_password(self.validated_data['new_password'])
        self.user.save()
        return self.user