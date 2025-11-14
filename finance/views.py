"""
ViewSets for the 'finance' app.

Handles core CRUD operations for finance models and custom actions like
locking/unlocking receipts and downloading PDFs.
"""

from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from api.permissions import IsStaffOrReadOnly, IsAdmin, IsStudent
from .models import FeesReceipt, Expense, Payroll, StockItem, StockTransaction, Reminder
from students.models import Student
from .serializers import (
    FeesReceiptSerializer, ExpenseSerializer, PayrollSerializer,
    StockItemSerializer, StockTransactionSerializer, ReminderSerializer
)
from .utils import generate_receipt_pdf_bytes
from django.http import HttpResponse, FileResponse
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
import logging

logger = logging.getLogger(__name__)


class FeesReceiptViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing FeesReceipts.
    - Staff/Admins have full CRUD access.
    - Students can access their own receipts via /my-receipts/.
    - Provides actions for locking, unlocking, and downloading PDFs.
    """
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
    @action(detail=True, methods=["post"], url_path="lock", permission_classes=[IsAdmin])
    def lock(self, request, pk=None):
        """(Admin Only) Locks a receipt, preventing further edits or deletion."""
        receipt = self.get_object()
        if receipt.locked:
            return Response({"detail": "Already locked."}, status=status.HTTP_400_BAD_REQUEST)
        receipt.locked = True
        receipt.save(update_fields=["locked"])
        return Response({"detail": "Receipt locked."}, status=status.HTTP_200_OK)

    @transaction.atomic
    @action(detail=True, methods=["post"], url_path="unlock", permission_classes=[IsAdmin])
    def unlock(self, request, pk=None):
        """(Admin Only) Unlocks a receipt, allowing edits."""
        receipt = self.get_object()
        if not receipt.locked:
            return Response({"detail": "Already unlocked."}, status=status.HTTP_400_BAD_REQUEST)
        receipt.locked = False
        receipt.save(update_fields=["locked"])
        return Response({"detail": "Receipt unlocked."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated], url_path="download")
    def download_pdf(self, request, pk=None):
        """
        Generates and returns a PDF receipt.
        Accessible by Admins OR the student who owns the receipt.
        
        It serves the pre-generated file if it exists, otherwise it
        generates, saves, and serves it.
        """
        receipt = get_object_or_404(FeesReceipt, pk=pk)

        # Permission check
        is_owner = (request.user.is_authenticated and 
                    hasattr(request.user, 'student') and 
                    request.user.student == receipt.student)
        is_admin = request.user.is_staff
        
        if not (is_owner or is_admin):
            return Response({"detail": "Not authorized to view this receipt."}, status=status.HTTP_403_FORBIDDEN)
            
        # 1. Try to serve the existing file
        if receipt.pdf_file:
            try:
                return FileResponse(
                    receipt.pdf_file.open('rb'), 
                    as_attachment=False, # Open inline
                    filename=f"{receipt.receipt_no}.pdf"
                )
            except FileNotFoundError:
                # File was deleted from storage, fall through to regenerate
                logger.warning(f"Receipt PDF file not found in storage: {receipt.pdf_file.name}")
                pass

        # 2. Fallback: Generate, save, and serve if missing
        logger.info(f"Generating PDF for receipt {receipt.receipt_no} on the fly.")
        pdf_bytes = generate_receipt_pdf_bytes(receipt.id)
        if not pdf_bytes:
            return Response({"detail": "Error generating PDF."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Save it for next time
        receipt.pdf_file.save(f"{receipt.receipt_no}.pdf", ContentFile(pdf_bytes), save=True)
        
        # Create and return the HTTP response
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{receipt.receipt_no}.pdf"'
        return response


class StudentReceiptsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only endpoint for a Student to view their own fee receipts.
    Accessed via /api/v1/my-receipts/
    """
    serializer_class = FeesReceiptSerializer
    permission_classes = [IsStudent] 
    
    def get_queryset(self):
        """Filters receipts for the currently authenticated student."""
        try:
            student_id = self.request.user.student.id
            return FeesReceipt.objects.filter(student_id=student_id).select_related(
                "student__user", "course", "batch"
            ).order_by("-date")
        except Student.DoesNotExist:
            return FeesReceipt.objects.none()


class ExpenseViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Expenses. (Staff/Admin only)
    """
    queryset = Expense.objects.select_related("added_by").all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ["category", "date"]
    search_fields = ["description"]
    ordering_fields = ["date", "amount"]


class PayrollViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Payroll. (Staff/Admin only)
    """
    queryset = Payroll.objects.select_related("trainer__user").all()
    serializer_class = PayrollSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ["month", "status", "trainer"]
    search_fields = ["trainer__user__first_name", "trainer__user__last_name", "trainer__emp_no"]
    ordering_fields = ["month", "net_pay"]


class StockItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing inventory StockItems. (Staff/Admin only)
    """
    queryset = StockItem.objects.all()
    serializer_class = StockItemSerializer
    permission_classes = [IsStaffOrReadOnly]
    search_fields = ["name", "description"]
    filterset_fields = ["unit_of_measure"]
    
    @action(detail=True, methods=["get"])
    def transactions(self, request, pk=None):
        """
        Returns a paginated list of transactions for a specific StockItem.
        """
        item = self.get_object()
        transactions = item.transactions.select_related("user").all()
        page = self.paginate_queryset(transactions)
        serializer = StockTransactionSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)


class StockTransactionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing StockTransactions. (Staff/Admin only)
    Creating/deleting transactions here will auto-update StockItem quantity.
    """
    queryset = StockTransaction.objects.select_related("item", "user")
    serializer_class = StockTransactionSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ["item", "user"]


class ReminderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only endpoint for viewing fee Reminders. (Admin only)
    """
    queryset = Reminder.objects.select_related(
        "student__user", "course", "batch", "sent_by"
    ).all()
    serializer_class = ReminderSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ["status", "student", "course", "batch"]
    search_fields = ["student__user__first_name", "student__user__last_name", "message"]
    ordering_fields = ["-sent_at"]