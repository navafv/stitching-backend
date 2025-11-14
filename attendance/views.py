"""
Views for the 'attendance' app.

Provides API endpoints for staff to manage attendance records
and for students to view their own attendance history.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Attendance, AttendanceEntry
from .serializers import AttendanceSerializer, StudentAttendanceEntrySerializer
from api.permissions import IsStaffOrReadOnly, IsStudent
from students.models import Student


class AttendanceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for staff to create, read, update, and delete attendance records.
    Read-only for non-staff users (if any permission).
    """
    queryset = (
        Attendance.objects
        .select_related("batch", "batch__course", "taken_by")
        .prefetch_related("entries", "entries__student", "entries__student__user")
        .order_by("-date")
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
    serializer_class = StudentAttendanceEntrySerializer
    permission_classes = [IsStudent] # Only students can access this

    def get_queryset(self):
        """
        Filters the queryset to only include entries for the
        currently authenticated student.
        """
        try:
            # Ensure the user has an associated student profile
            student_id = self.request.user.student.id
            return (
                AttendanceEntry.objects
                .filter(student_id=student_id)
                .select_related(
                    "attendance", 
                    "attendance__batch", 
                    "attendance__batch__course"
                )
                .order_by("-attendance__date")
            )
        except Student.DoesNotExist:
            # If user is not a student, return an empty queryset
            return AttendanceEntry.objects.none()
        except Exception:
            return AttendanceEntry.objects.none()