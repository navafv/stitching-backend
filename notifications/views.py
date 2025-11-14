"""
Views for the 'notifications' app.

Provides endpoints for:
- Users to list and manage their own notifications.
- Admins to send bulk notifications to various user groups.
"""

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer, NotificationCreateSerializer
from accounts.models import User, Role
from api.permissions import IsAdmin # Use a specific Admin permission

class NotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for users to manage their notifications.
    - GET: Lists notifications for the authenticated user.
    - POST: (Not typically used, notifications are system/admin generated).
    - PATCH/PUT: Can be used by the user to mark notifications as read.
    - DELETE: Allows a user to delete their own notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Overrides the default queryset to return *only* notifications
        for the currently authenticated user.
        """
        return Notification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        (Not typically used by end-users)
        Ensures a notification created via this endpoint
        is assigned to the request user.
        """
        serializer.save(user=self.request.user)

    @action(
        detail=False, 
        methods=["post"], 
        permission_classes=[IsAdmin], # Only Admins can send bulk messages
        url_path="send-bulk"
    )
    def send_bulk_notification(self, request):
        """
        (Admin Only) Admin action to send a notification to:
        - A specific user (`user_id`)
        - All users in a role (`role_id`)
        - All users in the system (`send_to_all`)
        """
        serializer = NotificationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        title = data.get("title")
        message = data.get("message")
        level = data.get("level")

        # Use a set to avoid sending duplicate notifications
        target_user_ids = set()

        if data.get("send_to_all"):
            target_user_ids.update(User.objects.values_list('id', flat=True))
        
        if data.get("user_id"):
            target_user_ids.add(data.get("user_id"))
            
        if data.get("role_id"):
            try:
                role = Role.objects.get(pk=data.get("role_id"))
                target_user_ids.update(role.get_user_ids())
            except Role.DoesNotExist:
                return Response(
                    {"detail": f"Role with id {data.get('role_id')} not found."}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Create a list of Notification objects to be created
        notifications_to_create = [
            Notification(
                user_id=user_id,
                title=title,
                message=message,
                level=level
            )
            for user_id in target_user_ids
        ]
        
        if notifications_to_create:
            # Use bulk_create for efficient insertion
            Notification.objects.bulk_create(notifications_to_create)
            return Response(
                {"detail": f"Successfully sent notification to {len(target_user_ids)} user(s)."},
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            {"detail": "No target users found for the specified criteria."}, 
            status=status.HTTP_400_BAD_REQUEST
        )