"""
UPDATED FILE: stitching-backend/courses/views.py
Added TeacherViewSet to provide data for the teacher portal.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Course, Trainer, Batch, Enrollment, BatchFeedback, Student
from .serializers import CourseSerializer, TrainerSerializer, BatchSerializer, EnrollmentSerializer, BatchFeedbackSerializer
# Import all permissions
from api.permissions import (
    IsAdminOrReadOnly, IsStaffOrReadOnly, IsEnrolledStudentOrReadOnly, 
    IsTeacher, IsAdmin, IsStudent
)
from students.serializers import StudentSerializer


class CourseViewSet(viewsets.ModelViewSet):
    """CRUD for Courses (admin-only writes)."""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAdminOrReadOnly] # Only superuser can write
    filterset_fields = ["active", "duration_weeks"]
    search_fields = ["code", "title"]
    ordering_fields = ["title", "duration_weeks", "total_fees"]


class TrainerViewSet(viewsets.ModelViewSet):
    """CRUD for Trainers (admin-only writes)."""
    queryset = Trainer.objects.select_related("user")
    serializer_class = TrainerSerializer
    permission_classes = [IsAdmin] # Only superuser can manage trainers
    filterset_fields = ["is_active", "join_date"]
    search_fields = ["emp_no", "user__first_name", "user__last_name"]
    ordering_fields = ["join_date", "emp_no", "id"]


class BatchViewSet(viewsets.ModelViewSet):
    """CRUD for Batches (admin-only writes)."""
    queryset = Batch.objects.select_related("course", "trainer", "trainer__user")
    serializer_class = BatchSerializer
    permission_classes = [IsAdmin] # Only superuser can manage batches
    filterset_fields = ["course", "trainer"]
    search_fields = ["code", "course__title", "trainer__user__first_name", "trainer__user__last_name"]
    ordering_fields = ["code"]


class EnrollmentViewSet(viewsets.ModelViewSet):
    """CRUD for Enrollments (admin-only writes)."""
    queryset = Enrollment.objects.select_related("student__user", "batch__course", "batch__trainer")
    serializer_class = EnrollmentSerializer
    filterset_fields = ["status", "batch", "student"]
    search_fields = ["student__user__first_name", "student__user__last_name", "batch__code"]
    ordering_fields = ["enrolled_on", "status"]

    def get_permissions(self):
        """
        Students can list their own enrollments.
        Admins can do anything.
        """
        if self.action == 'list':
            # Allow students OR admins to list
            self.permission_classes = [IsAdmin | IsStudent | IsTeacher]
        else:
            # Only admins can create, update, delete
            self.permission_classes = [IsAdmin]
        return super().get_permissions()
    
    def get_queryset(self):
        """
        Students only see their own enrollments.
        Admins see all enrollments.
        """
        user = self.request.user
        if not user.is_authenticated:
            return Enrollment.objects.none()
        
        if user.is_superuser:
            return super().get_queryset() # Admin sees all
        
        if user.is_staff and not user.is_superuser: # This is a Teacher
            return super().get_queryset() # Teacher also sees all (to manage)
        
        if not user.is_staff: # This is a Student
            try:
                # Filter by the student profile linked to this user
                student_id = user.student.id
                return super().get_queryset().filter(student_id=student_id)
            except Student.DoesNotExist:
                return Enrollment.objects.none() # User has no student profile

        return Enrollment.objects.none() # Default for other staff (like teachers)


class BatchFeedbackViewSet(viewsets.ModelViewSet):
    """
    API endpoint for students to submit feedback for batches.
    - Students can create/update their *own* feedback.
    - Staff can read all feedback.
    """
    queryset = BatchFeedback.objects.select_related(
        "enrollment__student__user", "enrollment__batch"
    )
    serializer_class = BatchFeedbackSerializer
    permission_classes = [IsEnrolledStudentOrReadOnly]

    def get_queryset(self):
        """
        Students can only list their own feedback.
        Staff can list all feedback.
        """
        user = self.request.user
        if not user.is_authenticated:
            return self.queryset.none()
        if user.is_staff:
            return self.queryset.all()
        return self.queryset.filter(enrollment__student__user=user)


class TeacherViewSet(viewsets.ViewSet):
    """
    Endpoints for the Teacher Portal.
    """
    permission_classes = [IsTeacher] # Only Teachers can access this

    @action(detail=False, methods=['get'], url_path='my-dashboard')
    def my_dashboard(self, request):
        """
        Provides summary data for the teacher's dashboard.
        """
        try:
            trainer = request.user.trainer
        except Trainer.DoesNotExist:
            return Response({"detail": "User is not a trainer."}, status=status.HTTP_400_BAD_REQUEST)

        all_assigned_batches = Batch.objects.filter(trainer=trainer)
        active_students_count = Enrollment.objects.filter(
            batch__in=all_assigned_batches, 
            status='active'
        ).distinct().count()
        active_batch_count = all_assigned_batches.count()

        return Response({
            "active_batch_count": active_batch_count,
            "active_student_count": active_students_count,
            "trainer_name": request.user.get_full_name()
        })

    @action(detail=False, methods=['get'], url_path='my-batches')
    def my_batches(self, request):
        """
        Returns a list of batches assigned to the currently logged-in trainer.
        """
        try:
            trainer = request.user.trainer
        except Trainer.DoesNotExist:
            return Response({"detail": "User is not a trainer."}, status=status.HTTP_400_BAD_REQUEST)
            
        batches = Batch.objects.filter(trainer=trainer).select_related("course").order_by('code')
        serializer = BatchSerializer(batches, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='my-batches/(?P<batch_pk>[^/.]+)/students')
    def my_batch_students(self, request, batch_pk=None):
        """
        Returns a list of students enrolled in a specific batch
        owned by the logged-in trainer.
        """
        try:
            trainer = request.user.trainer
        except Trainer.DoesNotExist:
            return Response({"detail": "User is not a trainer."}, status=status.HTTP_400_BAD_REQUEST)

        batch = Batch.objects.filter(pk=batch_pk, trainer=trainer).first()
        if not batch:
            return Response({"detail": "Batch not found or not assigned to you."}, status=status.HTTP_404_NOT_FOUND)

        students = Student.objects.filter(enrollments__batch=batch, enrollments__status='active').select_related('user')
        serializer = StudentSerializer(students, many=True, context={'request': request})
        return Response(serializer.data)