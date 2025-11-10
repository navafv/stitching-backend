"""
Attendance Analytics API
------------------------
Provides summary and performance statistics for dashboards.
"""

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Attendance, AttendanceEntry
from students.models import Student
from courses.models import Batch


class AttendanceAnalyticsViewSet(viewsets.ViewSet):
    """
    Provides analytical endpoints for attendance.
    Only accessible to authenticated users (typically staff).
    """
    permission_classes = [IsAuthenticated]

    # --------------------------------------------------------
    # 1. Batch summary — per student stats
    # --------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="batch/(?P<batch_id>[^/.]+)")
    def batch_summary(self, request, batch_id=None):
        """Returns batch-level attendance summary for all students."""
        batch = Batch.objects.filter(id=batch_id).first()
        if not batch:
            return Response({"detail": "Batch not found."}, status=404)

        attendance_days = Attendance.objects.filter(batch=batch).count()
        entries = (
            AttendanceEntry.objects
            .filter(attendance__batch=batch)
            .values("student__id", "student__user__first_name", "student__user__last_name")
            .annotate(
                presents=Count("id", filter=Q(status="P")),
                absents=Count("id", filter=Q(status="A")),
                leaves=Count("id", filter=Q(status="L")),
            )
        )

        for e in entries:
            total = e["presents"] + e["absents"] + e["leaves"]
            e["attendance_percentage"] = round((e["presents"] / total * 100) if total else 0, 2)

        data = {
            "batch": batch.code,
            "course": batch.course.title,
            "trainer": batch.trainer.user.get_full_name() if batch.trainer else None,
            "total_days": attendance_days,
            "students": list(entries),
        }
        return Response(data)

    # --------------------------------------------------------
    # 2. Student summary — per batch
    # --------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="student/(?P<student_id>[^/.]+)")
    def student_summary(self, request, student_id=None):
        """Returns student-level attendance summary across batches."""
        student = Student.objects.filter(id=student_id).first()
        if not student:
            return Response({"detail": "Student not found."}, status=404)

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
        )

        for e in entries:
            e["attendance_percentage"] = round((e["presents"] / e["total_days"] * 100) if e["total_days"] else 0, 2)

        data = {
            "student": student.user.get_full_name(),
            "reg_no": student.reg_no,
            "batches": list(entries),
        }
        return Response(data)

    # --------------------------------------------------------
    # 3. Batch timeline (for charts)
    # --------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="batch/(?P<batch_id>[^/.]+)/timeline")
    def batch_timeline(self, request, batch_id=None):
        """Returns attendance % over time for a batch (chart data)."""
        batch = Batch.objects.filter(id=batch_id).first()
        if not batch:
            return Response({"detail": "Batch not found."}, status=404)

        # Count presence % per date
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
            }
            for r in records
        ]

        return Response({
            "batch": batch.code,
            "course": batch.course.title,
            "timeline": data,
        })