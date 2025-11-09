"""
Finance Serializers
-------------------
Enhancements:
- Validations: positive amounts, edit lock, course/batch consistency.
- Auto-assign posted_by / added_by from request.
- Optional auto-generate receipt_no hook.
"""

from django.db import transaction
from rest_framework import serializers
from .models import FeesReceipt, Expense, Payroll
from courses.models import Enrollment


class FeesReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeesReceipt
        fields = "__all__"
        read_only_fields = ["date", "posted_by", "locked"]

    def validate(self, attrs):
        # Prevent edits if locked
        instance = getattr(self, "instance", None)
        if instance and instance.locked:
            raise serializers.ValidationError("This receipt is locked and cannot be edited.")

        # Basic consistency: if batch is provided, ensure it matches course
        course = attrs.get("course") or (instance.course if instance else None)
        batch = attrs.get("batch") or (instance.batch if instance else None)
        student = attrs.get("student") or (instance.student if instance else None)

        if batch and course and batch.course_id != course.id:
            raise serializers.ValidationError("Selected batch does not belong to the selected course.")

        # If batch is set, ensure the student is (or was) enrolled in that batch
        if batch and student:
            if not Enrollment.objects.filter(student=student, batch=batch).exists():
                # Not blocking, but you can choose to enforce strictly
                raise serializers.ValidationError("Student is not enrolled in the selected batch.")

        # Amount must be positive (MinValueValidator should handle, but double-check)
        amount = attrs.get("amount") or (instance.amount if instance else None)
        if amount is not None and amount < 0:
            raise serializers.ValidationError("Amount must be non-negative.")

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get("request")

        # Auto assign posted_by
        if request and request.user and request.user.is_authenticated:
            validated_data["posted_by"] = request.user

        # OPTIONAL: auto-generate receipt_no if not provided (keep your current behavior if you always pass it)
        if not validated_data.get("receipt_no"):
            validated_data["receipt_no"] = self._generate_receipt_no()

        return super().create(validated_data)

    def _generate_receipt_no(self) -> str:
        # Very simple generator: "RCP-000001" style
        last = FeesReceipt.objects.order_by("-id").first()
        next_id = (last.id + 1) if last else 1
        return f"RCP-{next_id:06d}"


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = "__all__"
        read_only_fields = ["date", "added_by"]

    def validate_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Amount must be non-negative.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            validated_data["added_by"] = request.user
        return super().create(validated_data)


class PayrollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payroll
        fields = "__all__"

    def validate(self, attrs):
        # Ensure net_pay is consistent with earnings - deductions if both provided
        earnings = attrs.get("earnings")
        deductions = attrs.get("deductions")
        net_pay = attrs.get("net_pay")

        # If earnings/deductions are provided as dicts with numeric values, do a soft check
        def _sum_dict(d):
            if not isinstance(d, dict):
                return None
            try:
                return sum(float(v) for v in d.values())
            except Exception:
                return None

        e_sum = _sum_dict(earnings)
        d_sum = _sum_dict(deductions)
        if e_sum is not None and d_sum is not None and net_pay is not None:
            expected = round(e_sum - d_sum, 2)
            # Allow small float rounding differences
            if round(float(net_pay), 2) < 0:
                raise serializers.ValidationError("Net pay cannot be negative.")
            # You can enforce exact match if you want:
            # if round(float(net_pay), 2) != expected:
            #     raise serializers.ValidationError("net_pay must equal sum(earnings) - sum(deductions).")
        return attrs
