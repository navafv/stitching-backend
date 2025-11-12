"""
Finance Outstanding Views
-------------------------
Tracks unpaid balances for students and batches
based on FeesReceipt and Course total fees.

FIX: Changed all @action decorators to detail=False to match
frontend API calls and fix 404 errors.
"""

from django.db.models import Sum, F
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from students.models import Student
from courses.models import Batch, Course, Enrollment
from .models import FeesReceipt


class OutstandingFeesViewSet(viewsets.ViewSet):
    """
    Provides endpoints for fee balance analytics:
    - per student
    - per batch
    - per course
    - overall
    """
    permission_classes = [IsAuthenticated]

    # ------------------------------------------------------------
    # 1️⃣ Student outstanding summary
    # ------------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="student/(?P<student_id>[^/.]+)")
    def student_outstanding(self, request, student_id=None):
        """Returns how much a student has paid and owes."""

        try:
            student_profile_id = request.user.student.id
        except Student.DoesNotExist:
            student_profile_id = None

        # Check permissions:
        # If the user is NOT an admin AND
        # (they are not a student OR they are requesting an ID that isn't theirs)
        if not request.user.is_superuser and (
            not student_profile_id or str(student_profile_id) != str(student_id)
        ):
            return Response(
                {"detail": "You do not have permission to view this financial data."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        student = Student.objects.filter(id=student_id).select_related("user").first()
        if not student:
            return Response({"detail": "Student not found."}, status=404)

        enrollments = Enrollment.objects.select_related("batch__course").filter(student=student)
        if not enrollments.exists():
            # Return empty data instead of 404, as this is valid
            return Response({
                "student": student.user.get_full_name(),
                "reg_no": student.reg_no,
                "courses": [],
                "total_paid": 0,
                "total_due": 0,
            })

        receipts = (
            FeesReceipt.objects.filter(student=student)
            .values("course_id")
            .annotate(total_paid=Sum("amount"))
        )
        paid_by_course = {r["course_id"]: float(r["total_paid"] or 0) for r in receipts}

        results = []
        total_due = 0
        total_paid = 0
        for e in enrollments:
            course = e.batch.course
            paid = paid_by_course.get(course.id, 0)
            due = float(course.total_fees) - paid
            total_due += max(due, 0)
            total_paid += paid
            results.append({
                "course": course.title,
                "batch": e.batch.code,
                "total_fees": float(course.total_fees),
                "paid": paid,
                "due": round(max(due, 0), 2),
            })

        data = {
            "student": student.user.get_full_name(),
            "reg_no": student.reg_no,
            "courses": results,
            "total_paid": round(total_paid, 2),
            "total_due": round(total_due, 2),
        }
        return Response(data)

    # ------------------------------------------------------------
    # 2️⃣ Batch-level outstanding summary
    # ------------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="batch/(?P<batch_id>[^/.]+)")
    def batch_outstanding(self, request, batch_id=None):
        """Returns outstanding fees summary for a batch."""
        batch = Batch.objects.filter(id=batch_id).select_related("course").first()
        if not batch:
            return Response({"detail": "Batch not found."}, status=404)

        enrollments = Enrollment.objects.filter(batch=batch).select_related("student__user")
        receipts = (
            FeesReceipt.objects.filter(batch=batch)
            .values("student_id")
            .annotate(total_paid=Sum("amount"))
        )
        paid_map = {r["student_id"]: float(r["total_paid"] or 0) for r in receipts}

        student_data = []
        total_fees = 0
        total_paid = 0
        for e in enrollments:
            course_fee = float(batch.course.total_fees)
            paid = paid_map.get(e.student.id, 0)
            due = course_fee - paid
            total_fees += course_fee
            total_paid += paid
            student_data.append({
                "student": e.student.user.get_full_name(),
                "reg_no": e.student.reg_no,
                "paid": round(paid, 2),
                "due": round(max(due, 0), 2),
            })

        data = {
            "batch": batch.code,
            "course": batch.course.title,
            "total_students": enrollments.count(),
            "total_fees": total_fees,
            "total_paid": total_paid,
            "total_due": round(total_fees - total_paid, 2),
            "students": student_data,
        }
        return Response(data)

    # ------------------------------------------------------------
    # 3️⃣ Course-level outstanding summary
    # ------------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="course/(?P<course_id>[^/.]+)")
    def course_outstanding(self, request, course_id=None):
        """Returns overall outstanding summary for a course."""
        course = Course.objects.filter(id=course_id).first()
        if not course:
            return Response({"detail": "Course not found."}, status=404)

        enrollments = Enrollment.objects.filter(batch__course=course)
        total_students = enrollments.count()

        receipts = (
            FeesReceipt.objects.filter(course=course)
            .aggregate(total_paid=Sum("amount"))
        )
        total_paid = float(receipts["total_paid"] or 0)
        total_expected = total_students * float(course.total_fees)
        total_due = total_expected - total_paid

        data = {
            "course": course.title,
            "total_students": total_students,
            "total_expected": total_expected,
            "total_paid": total_paid,
            "total_due": round(max(total_due, 0), 2),
        }
        return Response(data)

    # ------------------------------------------------------------
    # 4️⃣ Overall outstanding summary
    # ------------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="overall")
    def overall_outstanding(self, request):
        """Returns global outstanding summary for all courses."""
        courses = Course.objects.all()
        overall = []
        grand_expected = grand_paid = 0

        for course in courses:
            enrollments = Enrollment.objects.filter(batch__course=course)
            total_students = enrollments.count()
            total_expected = total_students * float(course.total_fees)
            total_paid = (
                FeesReceipt.objects.filter(course=course).aggregate(total=Sum("amount"))["total"]
                or 0
            )
            total_due = total_expected - float(total_paid or 0)

            overall.append({
                "course": course.title,
                "total_students": total_students,
                "expected": round(total_expected, 2),
                "paid": round(float(total_paid), 2),
                "due": round(max(total_due, 0), 2),
            })
            grand_expected += total_expected
            grand_paid += float(total_paid)

        return Response({
            "summary": overall,
            "grand_expected": round(grand_expected, 2),
            "grand_paid": round(grand_paid, 2),
            "grand_due": round(grand_expected - grand_paid, 2),
        })