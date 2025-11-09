from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allows read-only access to everyone, but restricts write
    (POST, PUT, DELETE) to admin users only.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


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
        return obj == request.user or (request.user and request.user.is_staff)
