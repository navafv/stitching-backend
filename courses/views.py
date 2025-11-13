"""
UPDATED FILE: stitching-backend/courses/views.py
Removed TeacherViewSet.
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
    IsAdmin, IsStudent # <-- 1. REMOVED IsTeacher
)
from students.serializers import StudentSerializer


class CourseViewSet(viewsets.ModelViewSet):
    # ... (no change)
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAdminOrReadOnly] 
    filterset_fields = ["active", "duration_weeks", "required_attendance_days"]
    search_fields = ["code", "title"]
    ordering_fields = ["title", "duration_weeks", "total_fees"]


class TrainerViewSet(viewsets.ModelViewSet):
    # ... (no change)
    queryset = Trainer.objects.select_related("user")
    serializer_class = TrainerSerializer
    permission_classes = [IsAdmin] 
    filterset_fields = ["is_active", "join_date"]
    search_fields = ["emp_no", "user__first_name", "user__last_name"]
    ordering_fields = ["join_date", "emp_no", "id"]


class BatchViewSet(viewsets.ModelViewSet):
    # ... (no change)
    queryset = Batch.objects.select_related("course", "trainer", "trainer__user")
    serializer_class = BatchSerializer
    permission_classes = [IsAdmin] 
    filterset_fields = ["course", "trainer"]
    search_fields = ["code", "course__title", "trainer__user__first_name", "trainer__user__last_name"]
    ordering_fields = ["code"]


class EnrollmentViewSet(viewsets.ModelViewSet):
    # ... (no change)
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
            self.permission_classes = [IsAdmin | IsStudent] # <-- 2. REMOVED IsTeacher
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
        
        # --- 3. SIMPLIFIED LOGIC ---
        if user.is_staff: # Any staff (admin)
            return super().get_queryset() # Admin sees all
        
        if not user.is_staff: # This is a Student
            try:
                # Filter by the student profile linked to this user
                student_id = user.student.id
                return super().get_queryset().filter(student_id=student_id)
            except Student.DoesNotExist:
                return Enrollment.objects.none() # User has no student profile

        return Enrollment.objects.none()


class BatchFeedbackViewSet(viewsets.ModelViewSet):
    # ... (no change)
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


# --- 4. REMOVED TeacherViewSet ---