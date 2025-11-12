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
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Role, User
from .serializers import (
    RoleSerializer, UserSerializer, UserCreateSerializer, 
    PasswordChangeSerializer, HistoricalUserSerializer
)
from api.permissions import IsAdmin
from rest_framework_simplejwt.authentication import JWTAuthentication


class RoleViewSet(viewsets.ModelViewSet):
    """Admin-only Role management."""
    queryset = Role.objects.all().order_by("name")
    serializer_class = RoleSerializer
    permission_classes = [IsAdmin]
    authentication_classes = [JWTAuthentication]
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
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.action in ["me", "partial_update", "set_password"]:
            return [IsAuthenticated()]
        return [IsAdmin()]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action == "set_password":
            return PasswordChangeSerializer
        return UserSerializer

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get the authenticated user's own profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=["post"], url_path="me/set-password")
    def set_password(self, request):
        """
        Allows the authenticated user to change their own password.
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class HistoricalUserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only view for User history.
    """
    queryset = User.history.select_related("history_user").all()
    serializer_class = HistoricalUserSerializer
    permission_classes = [IsAdmin]
    authentication_classes = [JWTAuthentication]
    filterset_fields = ["history_type", "history_user", "username"]
    search_fields = ["username", "first_name", "history_change_reason"]