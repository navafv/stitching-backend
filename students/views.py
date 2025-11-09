"""
Students Views
--------------
Enhancements:
- Restricted permissions (only staff can modify students).
- Uses select_related for performance.
- Added filter/search/order optimizations.
"""

from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAdminUser
from .models import Enquiry, Student, StudentMeasurement
from .serializers import EnquirySerializer, StudentSerializer, StudentMeasurementSerializer
from api.permissions import IsStaffOrReadOnly


class EnquiryViewSet(viewsets.ModelViewSet):
    """Handles public/student enquiries."""
    queryset = Enquiry.objects.all().order_by("-created_at")
    serializer_class = EnquirySerializer
    filterset_fields = ["status", "course_interest"]
    search_fields = ["name", "phone", "email", "notes"]
    ordering_fields = ["created_at", "name"]

    def get_permissions(self):
        """
        Allow public 'create' (POST) for the form.
        Require staff/admin for all other actions.
        """
        if self.action == 'create':
            # Anyone can POST to create a new enquiry
            self.permission_classes = [AllowAny]
        else:
            # Only staff/admin can list, view, update, or delete enquiries
            self.permission_classes = [IsAdminUser] 
            # Note: IsAdminUser in DRF checks if user.is_staff == True
        return super().get_permissions()


class StudentViewSet(viewsets.ModelViewSet):
    """CRUD for student records (staff-only modifications)."""
    queryset = Student.objects.select_related("user", "user__role")
    serializer_class = StudentSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ["active", "admission_date"]
    search_fields = [
        "reg_no",
        "user__first_name",
        "user__last_name",
        "guardian_name",
        "guardian_phone",
    ]
    ordering_fields = ["admission_date", "reg_no", "id"]


class StudentMeasurementViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing a student's measurements.
    Accessed via /api/v1/students/<student_id>/measurements/
    """
    queryset = StudentMeasurement.objects.all()
    serializer_class = StudentMeasurementSerializer
    permission_classes = [IsStaffOrReadOnly]

    def get_queryset(self):
        """Filter measurements by the student ID in the URL."""
        return self.queryset.filter(student_id=self.kwargs.get("student_pk"))

    def perform_create(self, serializer):
        """Automatically associate measurements with the student from the URL."""
        student = Student.objects.get(pk=self.kwargs.get("student_pk"))
        serializer.save(student=student)