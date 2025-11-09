"""
Accounts Views
--------------
Enhancements:
- Added selective permissions for safety.
- Optimized queryset (select_related for role).
- Added endpoint for self-profile retrieval.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from .models import Role, User
from .serializers import RoleSerializer, UserSerializer, UserCreateSerializer


class RoleViewSet(viewsets.ModelViewSet):
    """Admin-only Role management."""
    queryset = Role.objects.all().order_by("name")
    serializer_class = RoleSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ["name"]
    search_fields = ["name"]
    ordering_fields = ["name", "id"]


class UserViewSet(viewsets.ModelViewSet):
    """
    User management.
    Admins can manage all users.
    Authenticated users can view or update their own profile via /me endpoint.
    """
    queryset = User.objects.select_related("role")
    filterset_fields = ["is_active", "role"]
    search_fields = ["username", "email", "first_name", "last_name", "phone"]
    ordering_fields = ["id", "username", "first_name", "last_name"]

    def get_permissions(self):
        if self.action in ["me", "partial_update"]:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get the authenticated user's own profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
