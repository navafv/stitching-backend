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
            "is_staff", "is_superuser", "student_id",
        ]
        read_only_fields = ["id", "is_superuser"] 


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users (for Admins).
    Allows setting the is_staff flag for new teachers.
    """
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), source="role", write_only=True, required=False, allow_null=True
    )
    password = serializers.CharField(write_only=True)
    is_staff = serializers.BooleanField(default=False, required=False)

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "phone", "address", "role_id", "password", "is_staff",
        ]
        read_only_fields = ["id"]

    def validate_password(self, value):
        """Use Django's built-in validators."""
        validate_password(value)
        return value

    def create(self, validated_data):
        """Hashes password properly on creation."""
        password = validated_data.pop("password")
        user = User(**validated_data) # is_staff is set here
        user.set_password(password)
        user.save()
        return user


class StudentUserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users securely (for student conversion).
    Ensures is_staff is always False.
    """
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), source="role", write_only=True, required=False, allow_null=True
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

        validated_data['is_staff'] = False
        validated_data['is_superuser'] = False
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
    

class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint.
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate_new_password(self, value):
        # Use Django's built-in password validation
        validate_password(value)
        return value

    def validate(self, data):
        """
        Check that the old password is correct.
        """
        user = self.context['request'].user
        if not user.check_password(data.get('old_password')):
            raise serializers.ValidationError({"old_password": "Wrong password."})
        return data

    def save(self, **kwargs):
        """
        Save the new password.
        """
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
    

class HistoricalUserSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for displaying user history.
    """
    history_user_name = serializers.ReadOnlyField(source="history_user.username", allow_null=True)
    
    class Meta:
        model = User.history.model # Use the auto-created history model
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