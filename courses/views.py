"""
Courses Views
-------------
Enhancements:
- Querysets optimized with select_related and prefetch_related.
- Validation logic delegated to serializers.
- Scoped permissions (Admin vs Staff).
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Course, Trainer, Batch, Enrollment
from .serializers import CourseSerializer, TrainerSerializer, BatchSerializer, EnrollmentSerializer
from api.permissions import IsAdminOrReadOnly, IsStaffOrReadOnly


class CourseViewSet(viewsets.ModelViewSet):
    """CRUD for Courses (admin-only writes)."""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["active", "duration_weeks"]
    search_fields = ["code", "title"]
    ordering_fields = ["title", "duration_weeks", "total_fees"]


class TrainerViewSet(viewsets.ModelViewSet):
    """CRUD for Trainers (staff-only writes)."""
    queryset = Trainer.objects.select_related("user")
    serializer_class = TrainerSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ["is_active", "join_date"]
    search_fields = ["emp_no", "user__first_name", "user__last_name"]
    ordering_fields = ["join_date", "emp_no", "id"]


class BatchViewSet(viewsets.ModelViewSet):
    """CRUD for Batches."""
    queryset = Batch.objects.select_related("course", "trainer", "trainer__user")
    serializer_class = BatchSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ["course", "trainer", "start_date"]
    search_fields = ["code", "course__title", "trainer__user__first_name", "trainer__user__last_name"]
    ordering_fields = ["start_date", "end_date", "code"]


class EnrollmentViewSet(viewsets.ModelViewSet):
    """CRUD for Enrollments."""
    queryset = Enrollment.objects.select_related("student__user", "batch__course", "batch__trainer")
    serializer_class = EnrollmentSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ["status", "batch", "student"]
    search_fields = ["student__user__first_name", "student__user__last_name", "batch__code"]
    ordering_fields = ["enrolled_on", "status"]
