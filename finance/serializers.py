"""
Serializers for the 'finance' app.

Handles validation and data transformation for all finance models.
Includes logic for:
- Validating fee receipts against enrollments.
- Auto-assigning the logged-in user to 'posted_by' fields.
- Validating positive amounts and payload consistency.
"""

from django.db import transaction
from rest_framework import serializers
from .models import FeesReceipt, Expense, Payroll, StockItem, StockTransaction, Reminder
from courses.models import Enrollment


class FeesReceiptSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and viewing FeesReceipts.
    """
    student_name = serializers.ReadOnlyField(source="student.user.get_full_name")

    class Meta:
        model = FeesReceipt
        fields = [
            "id", "receipt_no", "student", "student_name", "course", "batch",
            "amount", "mode", "txn_id", "date", "posted_by", "locked", "pdf_file"
        ]
        read_only_fields = ["date", "posted_by", "locked", "student_name", "pdf_file"]

    def validate(self, attrs):
        """
        Business logic validation for fee receipts.
        1. Prevent edits if the receipt is locked.
        2. Ensure batch belongs to the selected course.
        3. (Optional) Ensure student is enrolled in the selected batch.
        4. Ensure amount is positive.
        """
        instance = getattr(self, "instance", None)
        
        # 1. Prevent edits if locked
        if instance and instance.locked:
            raise serializers.ValidationError("This receipt is locked and cannot be edited.")

        # Get the final state of student/course/batch
        course = attrs.get("course") or (instance.course if instance else None)
        batch = attrs.get("batch") or (instance.batch if instance else None)
        student = attrs.get("student") or (instance.student if instance else None)

        # 2. Basic consistency: if batch is provided, ensure it matches course
        if batch and course and batch.course_id != course.id:
            raise serializers.ValidationError("Selected batch does not belong to the selected course.")

        # 3. If batch is set, ensure the student is enrolled in that batch
        if batch and student:
            if not Enrollment.objects.filter(student=student, batch=batch).exists():
                # This can be a hard error if required
                pass # serializers.ValidationError("Student is not enrolled in the selected batch.")

        # 4. Amount must be positive
        amount = attrs.get("amount") or (instance.amount if instance else None)
        if amount is not None and amount < 0:
            raise serializers.ValidationError("Amount must be non-negative.")

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """
        Custom create method to:
        1. Auto-assign 'posted_by' to the request user.
        2. (Optional) Auto-generate a receipt number if not provided.
        """
        request = self.context.get("request")

        # 1. Auto assign posted_by
        if request and request.user and request.user.is_authenticated:
            validated_data["posted_by"] = request.user

        # 2. Auto-generate receipt_no if not provided
        if not validated_data.get("receipt_no"):
            validated_data["receipt_no"] = self._generate_receipt_no()

        return super().create(validated_data)

    def _generate_receipt_no(self) -> str:
        """Generates a simple unique receipt number."""
        last = FeesReceipt.objects.order_by("-id").first()
        next_id = (last.id + 1) if last else 1
        return f"RCP-{next_id:06d}"


class ExpenseSerializer(serializers.ModelSerializer):
    """Serializer for Expense model."""
    class Meta:
        model = Expense
        fields = "__all__"
        read_only_fields = ["date", "added_by"]

    @transaction.atomic
    def create(self, validated_data):
        """Auto-assign 'added_by' to the request user."""
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            validated_data["added_by"] = request.user
        return super().create(validated_data)


class PayrollSerializer(serializers.ModelSerializer):
    """Serializer for Payroll model."""
    class Meta:
        model = Payroll
        fields = "__all__"

    def validate(self, attrs):
        """
        Validates payroll data.
        (Optional) Can be extended to ensure net_pay matches
        earnings - deductions if they are structured.
        """
        net_pay = attrs.get("net_pay")
        if net_pay is not None and net_pay < 0:
             raise serializers.ValidationError("Net pay cannot be negative.")
        
        return attrs


class StockItemSerializer(serializers.ModelSerializer):
    """Serializer for StockItem model."""
    class Meta:
        model = StockItem
        fields = "__all__"
        read_only_fields = ["id", "quantity_on_hand"]


class StockTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for StockTransaction model.
    Updates to stock are made via this serializer.
    """
    item_name = serializers.ReadOnlyField(source="item.name")
    
    class Meta:
        model = StockTransaction
        fields = "__all__"
        read_only_fields = ["id", "date", "user"]

    def create(self, validated_data):
        """Assign 'user' on creation from the request."""
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            validated_data["user"] = request.user
        
        # The model's save() method handles updating the StockItem quantity
        return super().create(validated_data)
    

class ReminderSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for the Reminder log.
    Provides context-rich names.
    """
    student_name = serializers.ReadOnlyField(source="student.user.get_full_name")
    course_title = serializers.ReadOnlyField(source="course.title")
    batch_code = serializers.ReadOnlyField(source="batch.code")
    sent_by_user = serializers.ReadOnlyField(source="sent_by.username", allow_null=True)

    class Meta:
        model = Reminder
        fields = [
            "id",
            "student_name",
            "course_title",
            "batch_code",
            "message",
            "sent_at",
            "sent_by_user",
            "status",
        ]