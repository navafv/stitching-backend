"""
Views for the 'accounts' app.

Provides API endpoints for managing users, roles, and authentication
processes like password changes and resets.
"""

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import Role, User
from .serializers import (
    RoleSerializer, UserSerializer, UserCreateSerializer, 
    PasswordChangeSerializer, HistoricalUserSerializer,
    PasswordResetRequestSerializer, SetNewPasswordSerializer
)
from api.permissions import IsAdmin
from rest_framework_simplejwt.authentication import JWTAuthentication

# Password Reset Imports
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class RoleViewSet(viewsets.ModelViewSet):
    """API endpoint for Role management (Admin only)."""
    queryset = Role.objects.all().order_by("name")
    serializer_class = RoleSerializer
    permission_classes = [IsAdmin]
    authentication_classes = [JWTAuthentication]
    filterset_fields = ["name"]
    search_fields = ["name"]
    ordering_fields = ["name", "id"]


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for User management.
    - Admins can manage all users.
    - Authenticated users can view/update their own profile via `/api/v1/users/me/`.
    """
    queryset = User.objects.select_related("role").order_by('username')
    filterset_fields = ["is_active", "role"]
    search_fields = ["username", "email", "first_name", "last_name", "phone"]
    ordering_fields = ["id", "username", "first_name", "last_name"]
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        """Assign permissions based on the action."""
        if self.action in ["me", "set_password"]:
            return [IsAuthenticated()]
        return [IsAdmin()]

    def get_serializer_class(self):
        """Return the appropriate serializer for the action."""
        if self.action == "create":
            return UserCreateSerializer
        if self.action == "set_password":
            return PasswordChangeSerializer
        return UserSerializer

    @action(detail=False, methods=["get", "patch", "put"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Retrieve or update the profile for the authenticated user."""
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        # Handle PUT/PATCH for profile updates
        serializer = self.get_serializer(user, data=request.data, partial=request.method == 'PATCH')
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
    @action(detail=False, methods=["post"], url_path="me/set-password")
    def set_password(self, request):
        """Allows the authenticated user to change their own password."""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class HistoricalUserViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only endpoint for viewing User change history (Admin only)."""
    queryset = User.history.select_related("history_user").all()
    serializer_class = HistoricalUserSerializer
    permission_classes = [IsAdmin]
    authentication_classes = [JWTAuthentication]
    filterset_fields = ["history_type", "history_user", "username"]
    search_fields = ["username", "first_name", "history_change_reason"]


class ForgotPasswordView(generics.GenericAPIView):
    """
    Public endpoint to request a password reset email.
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = User.objects.get(email__iexact=serializer.validated_data['email'], is_active=True)
        
        token = PasswordResetTokenGenerator().make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Assumes the first configured origin is the frontend URL
        frontend_url = settings.CORS_ALLOWED_ORIGINS[0] 
        reset_link = f"{frontend_url}/reset-password/{uidb64}/{token}/"
        
        context = {
            'first_name': user.first_name or user.username,
            'reset_link': reset_link,
        }
        
        email_message_html = render_to_string('account/password_reset_email.html', context)
        email_message_plain = f"Click here to reset your password: {reset_link}"
        
        try:
            send_mail(
                subject="Password Reset for Noor Institute",
                message=email_message_plain,
                html_message=email_message_html,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )
        except Exception as e:
            logger.error(f"Failed to send password reset email to {user.email}: {e}")
            return Response(
                {"detail": "Error sending email. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {"detail": "Password reset link has been sent to your email."},
            status=status.HTTP_200_OK
        )


class ResetPasswordView(generics.GenericAPIView):
    """
    Public endpoint to confirm and set a new password using a token.
    """
    permission_classes = [AllowAny]
    serializer_class = SetNewPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            {"detail": "Password has been reset successfully. You can now log in."},
            status=status.HTTP_200_OK
        )