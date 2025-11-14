"""
Views for the 'events' app.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Event
from .serializers import EventSerializer
from api.permissions import IsAdminOrReadOnly # Use custom permission
from django.utils import timezone
from django.db.models import Q

class EventViewSet(viewsets.ModelViewSet):
    """
    API endpoint for institute events.
    - Admins can create, update, and delete events.
    - All users (including public/students) can read events.
    """
    serializer_class = EventSerializer
    permission_classes = [IsAdminOrReadOnly] # Only Admins can write
    
    def get_queryset(self):
        """
        Filters the visible events based on user role.
        - Admins see all events (past and future).
        - Students/Public see only *ongoing or future* events.
        """
        today = timezone.now().date()
        
        if self.request.user.is_authenticated and self.request.user.is_staff:
            # Admins see all events, newest first
            return Event.objects.all().order_by('-start_date')

        # For students/public, only show upcoming or ongoing events
        return Event.objects.filter(
            # Event ends today or in the future
            end_date__gte=today
        ).order_by('start_date') # Show nearest event first