"""
Read-only ViewSet for financial analytics and dashboard data.

Aggregates data from FeesReceipt, Expense, and Payroll to provide
high-level summaries and trend data.
"""

from django.db.models import Sum
from django.db.models.functions import TruncMonth
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import FeesReceipt, Expense, Payroll
from courses.models import Course, Trainer, Enrollment
from api.permissions import IsAdmin # Use a strict permission

class FinanceAnalyticsViewSet(viewsets.ViewSet):
    """
    Provides read-only financial analytics endpoints.
    Only accessible to authenticated Admin users.
    """
    permission_classes = [IsAdmin]

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        """
        Returns an overall summary of total income, total expenses,
        and net profit.
        """
        total_income = FeesReceipt.objects.aggregate(total=Sum("amount"))["total"] or 0
        total_expense = Expense.objects.aggregate(total=Sum("amount"))["total"] or 0
        total_payroll = Payroll.objects.aggregate(total=Sum("net_pay"))["total"] or 0

        # Combine payroll and other expenses into a single expense figure
        total_combined_expense = float(total_expense + total_payroll)
        total_income = float(total_income)

        data = {
            "total_income": total_income,
            "total_expense": total_combined_expense,
            "net_profit": round(total_income - total_combined_expense, 2),
        }
        return Response(data)

    @action(detail=False, methods=["get"], url_path="income-expense")
    def income_expense_timeline(self, request):
        """
        Returns monthly aggregated income vs. expense data,
        suitable for line or bar charts.
        """
        # 1. Aggregate monthly income from FeesReceipts
        income_data = (
            FeesReceipt.objects
            .annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(total_income=Sum("amount"))
            .order_by("month")
        )
        
        # 2. Aggregate monthly expenses from Expenses
        expense_data = (
            Expense.objects
            .annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(total_expense=Sum("amount"))
            .order_by("month")
        )
        
        # 3. Aggregate monthly payroll from Payroll
        # Payroll 'month' is a CharField "YYYY-MM", so we group by it directly
        payroll_data = (
            Payroll.objects
            .values("month")
            .annotate(total_payroll=Sum("net_pay"))
            .order_by("month")
        )
        
        # 4. Merge all data into a single timeline dictionary
        timeline = {}

        for rec in income_data:
            if not rec["month"]: continue
            key = rec["month"].strftime("%Y-%m")
            timeline.setdefault(key, {"month": key, "income": 0, "expense": 0, "payroll": 0})
            timeline[key]["income"] += float(rec["total_income"] or 0)

        for rec in expense_data:
            if not rec["month"]: continue
            key = rec["month"].strftime("%Y-%m")
            timeline.setdefault(key, {"month": key, "income": 0, "expense": 0, "payroll": 0})
            timeline[key]["expense"] += float(rec["total_expense"] or 0)

        for rec in payroll_data:
            if not rec["month"]: continue
            key = rec["month"] # This is already "YYYY-MM"
            timeline.setdefault(key, {"month": key, "income": 0, "expense": 0, "payroll": 0})
            timeline[key]["payroll"] += float(rec["total_payroll"] or 0)

        # 5. Calculate final net profit for each month
        for data in timeline.values():
            data["net_profit"] = round(data["income"] - (data["expense"] + data["payroll"]), 2)

        # Return a sorted list of the monthly data points
        return Response(sorted(timeline.values(), key=lambda x: x["month"]))

    @action(detail=False, methods=["get"], url_path="course/(?P<course_id>[^/.]+)")
    def course_summary(self, request, course_id=None):
        """
        Shows total income and student count for a specific course.
        """
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"detail": "Course not found."}, status=404)

        receipts = (
            FeesReceipt.objects.filter(course=course)
            .aggregate(total_income=Sum("amount"))
        )
        
        # Count unique students enrolled in this course
        active_students = Enrollment.objects.filter(
            batch__course=course,
            status="active"
        ).values("student").distinct().count()

        data = {
            "course": course.title,
            "total_income": float(receipts["total_income"] or 0),
            "active_students": active_students,
        }
        return Response(data)

    @action(detail=False, methods=["get"], url_path="trainer/(?P<trainer_id>[^/.]+)")
    def trainer_summary(self, request, trainer_id=None):
        """
        Summarizes payroll history for a specific trainer.
        """
        try:
            trainer = Trainer.objects.select_related("user").get(id=trainer_id)
        except Trainer.DoesNotExist:
            return Response({"detail": "Trainer not found."}, status=404)

        pay_records = (
            Payroll.objects.filter(trainer=trainer)
            .values("month", "status", "net_pay")
            .order_by("-month")
        )
        
        total_paid = sum(float(p["net_pay"]) for p in pay_records if p["net_pay"])

        data = {
            "trainer": trainer.user.get_full_name(),
            "emp_no": trainer.emp_no,
            "total_months": pay_records.count(),
            "total_paid": round(total_paid, 2),
            "records": list(pay_records),
        }
        return Response(data)