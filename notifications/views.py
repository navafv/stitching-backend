from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer, NotificationCreateSerializer
from accounts.models import User, Role

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(
        detail=False, 
        methods=["post"], 
        permission_classes=[IsAdminUser], 
        url_path="send-bulk"
    )
    def send_bulk_notification(self, request):
        """
        Admin action to send a notification to a user, a role, or all users.
        """
        serializer = NotificationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        title = data.get("title")
        message = data.get("message")
        level = data.get("level")

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
                    {"detail": "Role not found."}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Create notifications in bulk
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
            Notification.objects.bulk_create(notifications_to_create)
            return Response(
                {"detail": f"Successfully sent notification to {len(target_user_ids)} user(s)."},
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            {"detail": "No target users found."}, 
            status=status.HTTP_400_BAD_REQUEST
        )