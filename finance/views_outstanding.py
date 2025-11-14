"""
Read-only ViewSet for outstanding fee analytics.

Provides endpoints to calculate unpaid balances for students, batches,
and courses by comparing Course.total_fees against aggregated FeesReceipts.
"""

from django.db.models import Sum
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from students.models import Student
from courses.models import Batch, Course, Enrollment
from .models import FeesReceipt
from api.permissions import IsAdmin, IsStudent


class OutstandingFeesViewSet(viewsets.ViewSet):
    """
    Provides endpoints for fee balance analytics:
    - per student
    - per batch
    - per course
    - overall
    """
    permission_classes = [IsAdmin] # Default to Admin

    def get_permissions(self):
        """Allow students to access the 'student_outstanding' action."""
        if self.action == 'student_outstanding':
            return [IsAdmin() | IsStudent()]
        return super().get_permissions()

    @action(detail=False, methods=["get"], url_path="student/(?P<student_id>[^/.]+)")
    def student_outstanding(self, request, student_id=None):
        """
        Returns how much a specific student has paid and how much
        they still owe for their enrolled courses.
        
        Admins can view any student. Students can only view their own.
        """
        # Permission Check
        is_admin = request.user.is_staff
        is_owner = False
        try:
            is_owner = (request.user.student.id == int(student_id))
        except (AttributeError, ValueError, Student.DoesNotExist):
            pass

        if not (is_admin or is_owner):
            return Response(
                {"detail": "You do not have permission to view this financial data."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        student = Student.objects.filter(id=student_id).select_related("user").first()
        if not student:
            return Response({"detail": "Student not found."}, status=404)

        # Get all enrollments for the student
        enrollments = Enrollment.objects.select_related("batch__course").filter(student=student)
        if not enrollments.exists():
            return Response({
                "student": student.user.get_full_name(),
                "reg_no": student.reg_no,
                "courses": [],
                "total_paid": 0,
                "total_due": 0,
            })

        # Get all payments made by the student, grouped by course
        receipts = (
            FeesReceipt.objects.filter(student=student)
            .values("course_id")
            .annotate(total_paid=Sum("amount"))
        )
        paid_by_course = {r["course_id"]: float(r["total_paid"] or 0) for r in receipts}

        # Calculate due amount for each enrolled course
        results = []
        total_due = 0
        total_paid = 0
        
        # Use a set to avoid double-counting if enrolled in same course twice
        processed_course_ids = set() 

        for e in enrollments:
            course = e.batch.course
            if course.id in processed_course_ids:
                continue
            processed_course_ids.add(course.id)

            course_fee = float(course.total_fees)
            paid = paid_by_course.get(course.id, 0)
            due = course_fee - paid
            
            total_due += max(due, 0)
            total_paid += paid
            
            results.append({
                "course": course.title,
                "batch": e.batch.code, # Shows one of the batches
                "total_fees": course_fee,
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

    @action(detail=False, methods=["get"], url_path="batch/(?P<batch_id>[^/.]+)")
    def batch_outstanding(self, request, batch_id=None):
        """(Admin Only) Returns outstanding fees summary for all students in a batch."""
        batch = Batch.objects.filter(id=batch_id).select_related("course").first()
        if not batch:
            return Response({"detail": "Batch not found."}, status=404)

        enrollments = Enrollment.objects.filter(batch=batch).select_related("student__user")
        
        # Get payments made specifically for this batch
        receipts = (
            FeesReceipt.objects.filter(batch=batch)
            .values("student_id")
            .annotate(total_paid=Sum("amount"))
        )
        paid_map = {r["student_id"]: float(r["total_paid"] or 0) for r in receipts}

        student_data = []
        total_fees = 0
        total_paid = 0
        course_fee = float(batch.course.total_fees)

        for e in enrollments:
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
            "total_due": round(max(total_fees - total_paid, 0), 2),
            "students": student_data,
        }
        return Response(data)

    @action(detail=False, methods=["get"], url_path="course/(?P<course_id>[^/.]+)")
    def course_outstanding(self, request, course_id=None):
        """(Admin Only) Returns overall outstanding summary for a course."""
        course = Course.objects.filter(id=course_id).first()
        if not course:
            return Response({"detail": "Course not found."}, status=404)

        # Find all unique students ever enrolled in this course
        total_students = Enrollment.objects.filter(
            batch__course=course
        ).values("student").distinct().count()

        # Find all money received for this course
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

    @action(detail=False, methods=["get"], url_path="overall")
    def overall_outstanding(self, request):
        """(Admin Only) Returns global outstanding summary for all courses."""
        courses = Course.objects.all()
        overall = []
        grand_expected = 0.0
        grand_paid = 0.0

        for course in courses:
            # Get total expected fees based on unique student enrollments
            total_students = Enrollment.objects.filter(
                batch__course=course
            ).values("student").distinct().count()
            total_expected = total_students * float(course.total_fees)

            # Get total paid fees for this course
            total_paid = (
                FeesReceipt.objects.filter(course=course)
                .aggregate(total=Sum("amount"))["total"]
                or 0.0
            )
            total_paid = float(total_paid)
            total_due = total_expected - total_paid

            overall.append({
                "course": course.title,
                "total_students": total_students,
                "expected": round(total_expected, 2),
                "paid": round(total_paid, 2),
                "due": round(max(total_due, 0), 2),
            })
            grand_expected += total_expected
            grand_paid += total_paid

        return Response({
            "summary": overall,
            "grand_expected": round(grand_expected, 2),
            "grand_paid": round(grand_paid, 2),
            "grand_due": round(max(grand_expected - grand_paid, 0), 2),
        })