"""
Analytics-focused views for the 'attendance' app.

Provides aggregated data endpoints for dashboards and reports,
such as summaries by batch, student, or over time.
"""

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Attendance, AttendanceEntry
from students.models import Student
from courses.models import Batch
from api.permissions import IsStudent, IsAdmin # Assuming IsAdmin is preferred over IsAuthenticated


class AttendanceAnalyticsViewSet(viewsets.ViewSet):
    """
    Provides read-only analytical endpoints for attendance.
    Permissions are checked manually within each action.
    """
    permission_classes = [IsAuthenticated] # Base permission, refined in actions

    @action(detail=False, methods=["get"], permission_classes=[IsAdmin], url_path="batch/(?P<batch_id>[^/.]+)")
    def batch_summary(self, request, batch_id=None):
        """
        (Admin Only)
        Returns a batch-level attendance summary, calculating
        present, absent, and leave counts for each enrolled student.
        """
        batch = Batch.objects.filter(id=batch_id).select_related("course", "trainer__user").first()
        if not batch:
            return Response({"detail": "Batch not found."}, status=404)

        attendance_days = Attendance.objects.filter(batch=batch).count()
        
        # Aggregate attendance status for all students in this batch
        entries = (
            AttendanceEntry.objects
            .filter(attendance__batch=batch)
            .values("student__id", "student__user__first_name", "student__user__last_name", "student__reg_no")
            .annotate(
                presents=Count("id", filter=Q(status="P")),
                absents=Count("id", filter=Q(status="A")),
                leaves=Count("id", filter=Q(status="L")),
            )
            .order_by("student__user__first_name")
        )

        for e in entries:
            total = e["presents"] + e["absents"] + e["leaves"]
            e["attendance_percentage"] = round((e["presents"] / total * 100) if total else 0, 2)

        data = {
            "batch_code": batch.code,
            "course_title": batch.course.title,
            "trainer_name": batch.trainer.user.get_full_name() if batch.trainer else None,
            "total_attendance_days_taken": attendance_days,
            "students": list(entries),
        }
        return Response(data)

    @action(detail=False, methods=["get"], url_path="student/(?P<student_id>[^/.]+)")
    def student_summary(self, request, student_id=None):
        """
        (Admin or Owning Student)
        Returns a student-level attendance summary, aggregated by batch.
        """
        # Permission Check: Allow admin or the student themselves
        try:
            student_profile_id = request.user.student.id
        except Student.DoesNotExist:
            student_profile_id = None

        is_owner = str(student_profile_id) == str(student_id)
        is_admin = request.user.is_staff
        
        if not (is_owner or is_admin):
            return Response(
                {"detail": "You do not have permission to view this attendance data."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        student = Student.objects.filter(id=student_id).select_related("user").first()
        if not student:
            return Response({"detail": "Student not found."}, status=404)

        # Aggregate attendance status for this student, grouped by batch
        entries = (
            AttendanceEntry.objects
            .filter(student=student)
            .values("attendance__batch__id", "attendance__batch__code", "attendance__batch__course__title")
            .annotate(
                presents=Count("id", filter=Q(status="P")),
                absents=Count("id", filter=Q(status="A")),
                leaves=Count("id", filter=Q(status="L")),
                total_days=Count("id")
            )
            .order_by("-total_days")
        )

        for e in entries:
            e["attendance_percentage"] = round((e["presents"] / e["total_days"] * 100) if e["total_days"] else 0, 2)

        data = {
            "student_name": student.user.get_full_name(),
            "reg_no": student.reg_no,
            "batches": list(entries),
        }
        return Response(data)

    @action(detail=False, methods=["get"], permission_classes=[IsAdmin], url_path="batch/(?P<batch_id>[^/.]+)/timeline")
    def batch_timeline(self, request, batch_id=None):
        """
        (Admin Only)
        Returns attendance percentage over time for a batch, suitable for charts.
        """
        batch = Batch.objects.filter(id=batch_id).select_related("course").first()
        if not batch:
            return Response({"detail": "Batch not found."}, status=404)

        # Calculate percentage of 'Present' students for each day
        records = (
            Attendance.objects.filter(batch=batch)
            .values("date")
            .annotate(
                total=Count("entries"),
                presents=Count("entries", filter=Q(entries__status="P")),
            )
            .order_by("date")
        )

        data = [
            {
                "date": r["date"],
                "present_percentage": round((r["presents"] / r["total"] * 100) if r["total"] else 0, 2),
                "present_count": r["presents"],
                "total_marked": r["total"],
            }
            for r in records
        ]

        return Response({
            "batch_code": batch.code,
            "course_title": batch.course.title,
            "timeline": data,
        })