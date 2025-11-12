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
from .models import Attendance, AttendanceEntry
from .serializers import AttendanceSerializer, StudentAttendanceEntrySerializer
from api.permissions import IsStaffOrReadOnly, IsStudent


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


class StudentAttendanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only endpoint for a student to view their own attendance history.
    """
    queryset = AttendanceEntry.objects.all()
    serializer_class = StudentAttendanceEntrySerializer
    permission_classes = [IsStudent] # Only students can access this

    def get_queryset(self):
        """
        This is the key: filter the results to *only* entries
        that belong to the currently logged-in student.
        """
        try:
            student_id = self.request.user.student.id
            return (
                super()
                .get_queryset()
                .filter(student_id=student_id)
                .select_related(
                    "attendance", 
                    "attendance__batch", 
                    "attendance__batch__course"
                )
                .order_by("-attendance__date")
            )
        except Exception:
            # If user has no student profile or any other issue, return nothing
            return AttendanceEntry.objects.none()