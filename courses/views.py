"""
Views for the 'courses' app.

Provides API endpoints for:
- Course, Trainer, Batch, Enrollment (Staff/Admin CRUD)
- BatchFeedback (Student create, Staff read)
- CourseMaterial (Admin CRUD via nested route)
- StudentMaterials (Student-facing read-only list)
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from .models import (
    Course, Trainer, Batch, Enrollment, BatchFeedback, Student, CourseMaterial
)
from .serializers import (
    CourseSerializer, TrainerSerializer, BatchSerializer, 
    EnrollmentSerializer, BatchFeedbackSerializer, CourseMaterialSerializer
)
from api.permissions import (
    IsAdminOrReadOnly, IsStaffOrReadOnly, IsEnrolledStudentOrReadOnly, 
    IsAdmin, IsStudent
)
from django.http import FileResponse
from django.shortcuts import get_object_or_404
import logging

logger = logging.getLogger(__name__)


class CourseViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Courses.
    Write access is limited to Admins.
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAdminOrReadOnly] 
    filterset_fields = ["active", "duration_weeks", "required_attendance_days"]
    search_fields = ["code", "title"]
    ordering_fields = ["title", "duration_weeks", "total_fees"]


class TrainerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Trainers.
    Write access is limited to Admins.
    """
    queryset = Trainer.objects.select_related("user")
    serializer_class = TrainerSerializer
    permission_classes = [IsAdmin] 
    filterset_fields = ["is_active", "join_date"]
    search_fields = ["emp_no", "user__first_name", "user__last_name"]
    ordering_fields = ["join_date", "emp_no", "id"]


class BatchViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Batches.
    Write access is limited to Admins.
    """
    queryset = Batch.objects.select_related("course", "trainer", "trainer__user")
    serializer_class = BatchSerializer
    permission_classes = [IsAdmin] 
    filterset_fields = ["course", "trainer"]
    search_fields = ["code", "course__title", "trainer__user__first_name", "trainer__user__last_name"]
    ordering_fields = ["code"]


class EnrollmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Enrollments.
    - Admins can manage all.
    - Students can list their own.
    """
    queryset = Enrollment.objects.select_related("student__user", "batch__course", "batch__trainer")
    serializer_class = EnrollmentSerializer
    filterset_fields = ["status", "batch", "student"]
    search_fields = ["student__user__first_name", "student__user__last_name", "batch__code"]
    ordering_fields = ["enrolled_on", "status"]

    def get_permissions(self):
        """Admins can do anything, Students can only list/read."""
        if self.action == 'list':
            self.permission_classes = [IsAdmin | IsStudent]
        else:
            self.permission_classes = [IsAdmin]
        return super().get_permissions()
    
    def get_queryset(self):
        """
        Filters the queryset based on user role.
        - Admins see all enrollments.
        - Students see only their own enrollments.
        """
        user = self.request.user
        if not user.is_authenticated:
            return Enrollment.objects.none()
        
        if user.is_staff:
            return super().get_queryset()
        
        # User is a non-staff (Student)
        try:
            student_id = user.student.id
            return super().get_queryset().filter(student_id=student_id)
        except Student.DoesNotExist:
            return Enrollment.objects.none()


class BatchFeedbackViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Batch Feedback.
    - Students can create feedback for their own enrollments.
    - Staff can read all feedback.
    """
    queryset = BatchFeedback.objects.select_related(
        "enrollment__student__user", "enrollment__batch"
    )
    serializer_class = BatchFeedbackSerializer
    permission_classes = [IsEnrolledStudentOrReadOnly] # Custom permission handles logic

    def get_queryset(self):
        """
        - Staff see all feedback.
        - Students (non-staff) see only their own feedback.
        """
        user = self.request.user
        if not user.is_authenticated:
            return self.queryset.none()
        if user.is_staff:
            return self.queryset.all()
        return self.queryset.filter(enrollment__student__user=user)


class CourseMaterialViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Course Materials.
    Accessed via nested route: /api/v1/courses/<course_pk>/materials/
    - Admins have full CRUD access.
    - Enrolled Students have read/download access.
    """
    queryset = CourseMaterial.objects.all()
    serializer_class = CourseMaterialSerializer
    parser_classes = [MultiPartParser, FormParser] # For file uploads

    def get_permissions(self):
        """Admins can manage, Authenticated users can read/download."""
        if self.action in ['list', 'retrieve', 'download']:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [IsAdmin]
        return super().get_permissions()

    def get_queryset(self):
        """Filter materials by the course_pk in the URL."""
        return self.queryset.filter(
            course_id=self.kwargs.get("course_pk")
        ).select_related("course")

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def download(self, request, course_pk=None, pk=None):
        """
        Securely downloads the file for this material.
        Accessible by Admins, or Students actively enrolled in this course.
        """
        material = get_object_or_404(CourseMaterial, course_id=course_pk, pk=pk)
        
        if not material.file:
            return Response({"detail": "This material is a link, not a file."}, status=status.HTTP_404_NOT_FOUND)

        # Permission Check: Allow admins or enrolled students
        is_admin = request.user.is_staff
        is_enrolled = False
        if not is_admin:
            try:
                student = request.user.student
                # Check for an *active* enrollment in this course
                is_enrolled = Enrollment.objects.filter(
                    student=student, 
                    batch__course_id=course_pk,
                    status="active"
                ).exists()
            except Student.DoesNotExist:
                is_enrolled = False
        
        if not (is_admin or is_enrolled):
            return Response({"detail": "Not authorized to download this file."}, status=status.HTTP_403_FORBIDDEN)

        try:
            # Use FileResponse to stream the file efficiently
            return FileResponse(
                material.file.open('rb'), 
                as_attachment=True, 
                filename=material.file.name.split('/')[-1]
            )
        except FileNotFoundError:
            logger.warning(f"CourseMaterial file not found in storage: {material.file.name}")
            return Response({"detail": "File not found on server."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error accessing material file {material.file.name}: {e}")
            return Response({"detail": f"Error accessing file: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StudentMaterialsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only endpoint for a Student to see all materials
    for their *actively enrolled* courses.
    Accessed via: /api/v1/my-materials/
    """
    serializer_class = CourseMaterialSerializer
    permission_classes = [IsStudent]

    def get_queryset(self):
        """
        Filters materials to only those for which the student
        has an active enrollment.
        """
        try:
            student = self.request.user.student
            # Get IDs of all courses the student is actively enrolled in
            enrolled_course_ids = Enrollment.objects.filter(
                student=student,
                status="active"
            ).values_list("batch__course_id", flat=True).distinct()
            
            return CourseMaterial.objects.filter(
                course_id__in=enrolled_course_ids
            ).select_related("course").order_by("course__title", "-uploaded_at")
            
        except Student.DoesNotExist:
            return CourseMaterial.objects.none()