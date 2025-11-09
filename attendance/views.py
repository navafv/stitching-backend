"""
Attendance Views
----------------
Enhancements:
- select_related optimizations for joined lookups.
- Restricted to staff for write access.
- Added filtering and ordering.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Attendance
from .serializers import AttendanceSerializer
from api.permissions import IsStaffOrReadOnly


class AttendanceViewSet(viewsets.ModelViewSet):
    """CRUD for attendance records."""
    queryset = (
        Attendance.objects
        .select_related("batch", "batch__course", "taken_by")
        .prefetch_related("entries", "entries__student", "entries__student__user")
    )
    serializer_class = AttendanceSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ["batch", "date", "batch__course"]
    search_fields = ["batch__code", "remarks", "taken_by__username"]
    ordering_fields = ["date", "id"]
