"""
UPDATED FILE: stitching-backend/api/permissions.py
Added IsAdmin, IsTeacher, and IsStudent permissions for granular access.
"""
from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allows read-only access to everyone, but restricts write
    (POST, PUT, DELETE) to admin users only.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_superuser) # CHANGED: from is_staff

class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Allows read-only access to everyone, but write access to staff or superusers.
    Perfect for management-level models (like Attendance, Students, etc.)
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and (request.user.is_staff or request.user.is_superuser))


class IsSelfOrAdmin(permissions.BasePermission):
    """
    Allows a user to access their own data, or admin users to access anyone's.
    Use this for profile or user-specific endpoints.
    """
    def has_object_permission(self, request, view, obj):
        # Handle case where obj is User
        if hasattr(obj, 'is_superuser'):
            return obj == request.user or (request.user and request.user.is_superuser)
        # Handle case where obj is owned by a user
        if hasattr(obj, 'user'):
            return obj.user == request.user or (request.user and request.user.is_superuser)
        return False


class IsEnrolledStudentOrReadOnly(permissions.BasePermission):
    """
    Allows read-only access to staff, but write access only to the
    student associated with the enrollment.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_staff)
        # Allow POST if authenticated
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Read-only for staff
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_staff)
        # Write permissions only for the student who owns the enrollment
        return obj.enrollment.student.user == request.user

# --- NEW PERMISSIONS ---

class IsAdmin(permissions.BasePermission):
    """Allows access only to Admin users (Superusers)."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)

class IsTeacher(permissions.BasePermission):
    """Allows access only to Teachers (Staff but not Superuser)."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff and not request.user.is_superuser)

class IsStudent(permissions.BasePermission):
    """Allows access only to Students (Not Staff)."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and not request.user.is_staff)