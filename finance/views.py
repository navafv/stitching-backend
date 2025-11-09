"""
Finance ViewSets
----------------
Enhancements:
- Query optimization with select_related.
- Staff-only write access via IsStaffOrReadOnly.
- Lock/Unlock actions on receipts.
"""

from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from api.permissions import IsStaffOrReadOnly
from .models import FeesReceipt, Expense, Payroll
from .serializers import FeesReceiptSerializer, ExpenseSerializer, PayrollSerializer


class FeesReceiptViewSet(viewsets.ModelViewSet):
    queryset = (
        FeesReceipt.objects
        .select_related("student__user", "course", "batch", "posted_by")
        .all()
    )
    serializer_class = FeesReceiptSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ["mode", "locked", "date", "student", "course", "batch"]
    search_fields = ["receipt_no", "txn_id", "student__user__username", "student__reg_no"]
    ordering_fields = ["date", "amount", "receipt_no"]

    @transaction.atomic
    @action(detail=True, methods=["post"], url_path="lock")
    def lock(self, request, pk=None):
        """Locks a receipt to prevent further edits or deletion."""
        receipt = self.get_object()
        if receipt.locked:
            return Response({"detail": "Already locked."}, status=status.HTTP_200_OK)
        receipt.locked = True
        receipt.save(update_fields=["locked"])
        return Response({"detail": "Receipt locked."}, status=status.HTTP_200_OK)

    @transaction.atomic
    @action(detail=True, methods=["post"], url_path="unlock")
    def unlock(self, request, pk=None):
        """Unlocks a receipt (use sparingly; consider admin-only in production)."""
        receipt = self.get_object()
        if not receipt.locked:
            return Response({"detail": "Already unlocked."}, status=status.HTTP_200_OK)
        receipt.locked = False
        receipt.save(update_fields=["locked"])
        return Response({"detail": "Receipt unlocked."}, status=status.HTTP_200_OK)


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ["category", "date"]
    search_fields = ["description"]
    ordering_fields = ["date", "amount"]


class PayrollViewSet(viewsets.ModelViewSet):
    queryset = Payroll.objects.select_related("trainer__user").all()
    serializer_class = PayrollSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ["month", "status", "trainer"]
    search_fields = ["trainer__user__first_name", "trainer__user__last_name", "trainer__emp_no"]
    ordering_fields = ["month", "net_pay"]
