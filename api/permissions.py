"""
UPDATED FILE: stitching-backend/api/permissions.py
Removed IsTeacher permission.
"""
from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    # ... (no change)
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_superuser) 

class IsStaffOrReadOnly(permissions.BasePermission):
    # ... (no change)
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and (request.user.is_staff or request.user.is_superuser))


class IsSelfOrAdmin(permissions.BasePermission):
    # ... (no change)
    def has_object_permission(self, request, view, obj):
        # Handle case where obj is User
        if hasattr(obj, 'is_superuser'):
            return obj == request.user or (request.user and request.user.is_superuser)
        # Handle case where obj is owned by a user
        if hasattr(obj, 'user'):
            return obj.user == request.user or (request.user and request.user.is_superuser)
        return False


class IsEnrolledStudentOrReadOnly(permissions.BasePermission):
    # ... (no change)
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
    # ... (no change)
    """Allows access only to Admin users (Superusers)."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)

# --- REMOVED IsTeacher ---

class IsStudent(permissions.BasePermission):
    # ... (no change)
    """Allows access only to Students (Not Staff)."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and not request.user.is_staff)