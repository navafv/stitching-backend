"""
Custom permissions for the API.

Defines granular access control rules for different user types
(e.g., Admin, Staff, Student) and object-level ownership.
"""

from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allows read-only access to anyone, but write access only to Superusers.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_superuser) 

class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Allows read-only access to anyone, but write access only to Staff or Superusers.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and (request.user.is_staff or request.user.is_superuser))


class IsSelfOrAdmin(permissions.BasePermission):
    """
    Allows access only to the object's owner or an Admin.
    Assumes the object has a 'user' attribute.
    """
    def has_object_permission(self, request, view, obj):
        # Handle case where obj is the User model itself
        if isinstance(obj, permissions.get_user_model()):
            return obj == request.user or (request.user and request.user.is_superuser)
        
        # Handle case where obj has a 'user' foreign key
        if hasattr(obj, 'user'):
            return obj.user == request.user or (request.user and request.user.is_superuser)
        
        # Handle case where obj has a 'student' foreign key (which links to user)
        if hasattr(obj, 'student') and hasattr(obj.student, 'user'):
             return obj.student.user == request.user or (request.user and request.user.is_superuser)

        return False


class IsEnrolledStudentOrReadOnly(permissions.BasePermission):
    """
    - Read access: Staff only.
    - Write access (POST): Any authenticated user.
    - Object-level write (PUT/PATCH/DELETE): Only the student who
      owns the related enrollment.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            # Read-only for staff
            return bool(request.user and request.user.is_staff)
        # Allow POST (create) if authenticated
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # Read-only for staff
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_staff)
        
        # Write permissions only for the student who owns the enrollment
        if hasattr(obj, 'enrollment'):
            return obj.enrollment.student.user == request.user
        return False


class IsAdmin(permissions.BasePermission):
    """Allows access only to Admin users (Superusers)."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class IsStudent(permissions.BasePermission):
    """Allows access only to authenticated non-Staff users (Students)."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and not request.user.is_staff)