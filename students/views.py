"""
Students Views
--------------
Enhancements:
- Restricted permissions (only staff can modify students).
- Uses select_related for performance.
- Added filter/search/order optimizations.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Enquiry, Student
from .serializers import EnquirySerializer, StudentSerializer
from api.permissions import IsStaffOrReadOnly


class EnquiryViewSet(viewsets.ModelViewSet):
    """Handles public/student enquiries."""
    queryset = Enquiry.objects.all().order_by("-created_at")
    serializer_class = EnquirySerializer
    permission_classes = [IsAuthenticated]  # or IsStaffOrReadOnly if needed
    filterset_fields = ["status", "course_interest"]
    search_fields = ["name", "phone", "email", "notes"]
    ordering_fields = ["created_at", "name"]


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
