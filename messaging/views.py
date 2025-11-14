"""
Views for the 'messaging' app.

Provides endpoints for:
- Admins to list all conversations.
- Students to get their single, dedicated conversation.
- Both parties to list and create messages within a conversation.
"""

from rest_framework import viewsets, status, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer, StudentConversationSerializer
from api.permissions import IsAdmin, IsStudent
from students.models import Student

class ConversationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet for managing conversations.
    - Admins can list and retrieve all conversations.
    - Students can list/retrieve *only* their own conversation.
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Admins get a list-oriented serializer (ConversationSerializer).
        Students get a detailed serializer with nested messages
        (StudentConversationSerializer).
        """
        if self.request.user.is_staff:
            return ConversationSerializer
        return StudentConversationSerializer

    def get_queryset(self):
        """
        Filters conversations based on user role.
        """
        user = self.request.user
        if user.is_staff:
            # Admins see all conversations, ordered by most recent
            return Conversation.objects.select_related("student__user").order_by('-last_message_at')
        
        # Students only see their own conversation
        try:
            student = user.student
            return Conversation.objects.filter(student=student).prefetch_related("messages")
        except Student.DoesNotExist:
            return Conversation.objects.none()

    @action(detail=False, methods=['get'], url_path='my-conversation', permission_classes=[IsStudent])
    def my_conversation(self, request):
        """
        A specific endpoint for students to get-or-create their
        dedicated conversation thread.
        """
        try:
            student = request.user.student
        except Student.DoesNotExist:
             return Response({"detail": "Student profile not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Get or create the conversation for this student
        conversation, created = Conversation.objects.get_or_create(student=student)
        
        # When student views it, mark messages as read for them
        conversation.mark_as_read_by(request.user)
        
        serializer = StudentConversationSerializer(conversation, context={'request': request})
        return Response(serializer.data)


class MessageViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin):
    """
    ViewSet for listing and creating messages within a conversation.
    Accessed via nested route:
    /api/v1/conversations/<conversation_pk>/messages/
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_conversation(self):
        """
        Helper method to get the parent conversation from the URL
        and verify the user has permission to access it.
        """
        conversation_id = self.kwargs.get('conversation_pk')
        user = self.request.user
        
        try:
            conversation = Conversation.objects.select_related("student__user").get(pk=conversation_id)
        except Conversation.DoesNotExist:
            return None
            
        # Security check: User must be an admin OR the student in this conversation
        if user.is_staff or (hasattr(user, 'student') and conversation.student == user.student):
            return conversation
        
        return None

    def get_queryset(self):
        """
        Return messages only for the conversation specified in the URL.
        """
        conversation = self.get_conversation()
        if conversation:
            # Mark as read when messages are listed by this user
            conversation.mark_as_read_by(self.request.user)
            return conversation.messages.select_related('sender').order_by('sent_at')
        return Message.objects.none()

    def get_serializer_context(self):
        """Pass the conversation object to the serializer for context."""
        context = super().get_serializer_context()
        context['conversation'] = self.get_conversation()
        return context

    def create(self, request, *args, **kwargs):
        """
        Create a new message.
        The sender is automatically set to request.user.
        """
        conversation = self.get_conversation()
        if not conversation:
            return Response({"detail": "Conversation not found or access denied."}, status=status.HTTP_404_NOT_FOUND)
        
        return super().create(request, *args, **kwargs)