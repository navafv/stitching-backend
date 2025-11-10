"""
Finance Analytics Views
-----------------------
Provides financial reports and KPIs for dashboards.
Aggregates data from FeesReceipt, Expense, and Payroll.
"""

from datetime import date
from django.db.models import Sum, F, Q
from django.db.models.functions import TruncMonth
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import FeesReceipt, Expense, Payroll
from courses.models import Course, Trainer


class FinanceAnalyticsViewSet(viewsets.ViewSet):
    """
    Provides read-only financial analytics endpoints.
    Only accessible to authenticated (usually staff/admin) users.
    """
    permission_classes = [IsAuthenticated]

    # ------------------------------------------------------------
    # 1️⃣ General summary endpoint
    # ------------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        """Returns overall income, expense, and profit summary."""

        total_income = FeesReceipt.objects.aggregate(total=Sum("amount"))["total"] or 0
        total_expense = Expense.objects.aggregate(total=Sum("amount"))["total"] or 0
        total_payroll = Payroll.objects.aggregate(total=Sum("net_pay"))["total"] or 0

        data = {
            "total_income": float(total_income),
            "total_expense": float(total_expense + total_payroll),
            "net_profit": round(float(total_income) - float(total_expense + total_payroll), 2),
        }
        return Response(data)

    # ------------------------------------------------------------
    # 2️⃣ Monthly income/expense trend (for line charts)
    # ------------------------------------------------------------
    @action(detail=False, methods=["get"], url_path="income-expense")
    def income_expense(self, request):
        """
        Returns monthly aggregated income vs expense data.
        Used for trend charts (e.g., line/bar charts in React).
        """

        income = (
            FeesReceipt.objects
            .annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(total_income=Sum("amount"))
            .order_by("month")
        )
        expense = (
            Expense.objects
            .annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(total_expense=Sum("amount"))
            .order_by("month")
        )
        
        # --- FIX: Simplified the payroll query ---
        payroll = (
            Payroll.objects
            .values("month")
            .annotate(total_payroll=Sum("net_pay"))
            .order_by("month")
        )
        # --- END FIX ---

        # merge all month data into one timeline
        result = {}
        for rec in income:
            if not rec["month"]: continue # Skip any null dates
            key = rec["month"].strftime("%Y-%m")
            result.setdefault(key, {"month": key, "income": 0, "expense": 0, "payroll": 0})
            result[key]["income"] = float(rec["total_income"] or 0)
        for rec in expense:
            if not rec["month"]: continue # Skip any null dates
            key = rec["month"].strftime("%Y-%m")
            result.setdefault(key, {"month": key, "income": 0, "expense": 0, "payroll": 0})
            result[key]["expense"] = float(rec["total_expense"] or 0)
        for rec in payroll:
            if not rec["month"]: continue # Skip any null months
            key = rec["month"] # This is already a 'YYYY-MM' string
            result.setdefault(key, {"month": key, "income": 0, "expense": 0, "payroll": 0})
            result[key]["payroll"] = float(rec["total_payroll"] or 0)

        # compute net
        for month, data in result.items():
            data["net_profit"] = round(data["income"] - (data["expense"] + data["payroll"]), 2)

        return Response(sorted(result.values(), key=lambda x: x["month"]))

    # ------------------------------------------------------------
    # 3️⃣ Course revenue report
    # ------------------------------------------------------------
    @action(detail=True, methods=["get"], url_path="course/(?P<course_id>[^/.]+)")
    def course_summary(self, request, course_id=None):
        """Shows total income received per course."""
        course = Course.objects.filter(id=course_id).first()
        if not course:
            return Response({"detail": "Course not found."}, status=404)

        receipts = (
            FeesReceipt.objects.filter(course=course)
            .aggregate(total_income=Sum("amount"))
        )
        data = {
            "course": course.title,
            "total_income": float(receipts["total_income"] or 0),
            "active_students": course.batches.values("enrollments__student").distinct().count(),
        }
        return Response(data)

    # ------------------------------------------------------------
    # 4️⃣ Trainer payroll summary
    # ------------------------------------------------------------
    @action(detail=True, methods=["get"], url_path="trainer/(?P<trainer_id>[^/.]+)")
    def trainer_summary(self, request, trainer_id=None):
        """Summarizes payroll for a specific trainer."""
        trainer = Trainer.objects.filter(id=trainer_id).first()
        if not trainer:
            return Response({"detail": "Trainer not found."}, status=404)

        pay = (
            Payroll.objects.filter(trainer=trainer)
            .values("month", "status")
            .annotate(total_paid=Sum("net_pay"))
            .order_by("-month")
        )

        data = {
            "trainer": trainer.user.get_full_name(),
            "emp_no": trainer.emp_no,
            "total_months": len(pay),
            "total_paid": round(sum(float(p["total_paid"]) for p in pay), 2),
            "records": list(pay),
        }
        return Response(data)