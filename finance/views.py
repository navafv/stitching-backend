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
from .models import FeesReceipt, Expense, Payroll, StockItem, StockTransaction
from .serializers import FeesReceiptSerializer, ExpenseSerializer, PayrollSerializer, StockItemSerializer, StockTransactionSerializer


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


class StockItemViewSet(viewsets.ModelViewSet):
    """
    Manage Inventory Stock Items. Quantity is read-only and updated by Transactions.
    """
    queryset = StockItem.objects.all()
    serializer_class = StockItemSerializer
    permission_classes = [IsStaffOrReadOnly]
    search_fields = ["name", "description"]
    filterset_fields = ["unit_of_measure"]
    
    @action(detail=True, methods=["get"])
    def transactions(self, request, pk=None):
        """Get all transactions for a specific stock item."""
        item = self.get_object()
        transactions = item.transactions.all()
        page = self.paginate_queryset(transactions)
        serializer = StockTransactionSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)


class StockTransactionViewSet(viewsets.ModelViewSet):
    """
    Create transactions to add/remove stock.
    This will automatically update the quantity_on_hand of the StockItem.
    """
    queryset = StockTransaction.objects.select_related("item", "user")
    serializer_class = StockTransactionSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ["item", "user"]