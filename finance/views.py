"""
Finance ViewSets
----------------
UPDATED: download_pdf action now serves the pre-generated file.
"""

from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from api.permissions import IsStaffOrReadOnly, IsAdmin, IsStudent
from .models import FeesReceipt, Expense, Payroll, StockItem, StockTransaction, Reminder
from .serializers import FeesReceiptSerializer, ExpenseSerializer, PayrollSerializer, StockItemSerializer, StockTransactionSerializer, ReminderSerializer
from .utils import generate_receipt_pdf_bytes
from django.http import HttpResponse
# --- 1. IMPORT ContentFile ---
from django.core.files.base import ContentFile


class FeesReceiptViewSet(viewsets.ModelViewSet):
    # ... (no change to queryset, serializer_class, etc.) ...
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
        # ... (no change)
        receipt = self.get_object()
        if receipt.locked:
            return Response({"detail": "Already locked."}, status=status.HTTP_200_OK)
        receipt.locked = True
        receipt.save(update_fields=["locked"])
        return Response({"detail": "Receipt locked."}, status=status.HTTP_200_OK)

    @transaction.atomic
    @action(detail=True, methods=["post"], url_path="unlock")
    def unlock(self, request, pk=None):
        # ... (no change)
        receipt = self.get_object()
        if not receipt.locked:
            return Response({"detail": "Already unlocked."}, status=status.HTTP_200_OK)
        receipt.locked = False
        receipt.save(update_fields=["locked"])
        return Response({"detail": "Receipt unlocked."}, status=status.HTTP_200_OK)

    # --- 2. UPDATE download_pdf ACTION ---
    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated], url_path="download")
    def download_pdf(self, request, pk=None):
        """
        Generates and returns a PDF receipt.
        Accessible by Admins OR the student who owns the receipt.
        """
        receipt = self.get_object()

        # Permission check
        is_owner = request.user == receipt.student.user
        is_admin = request.user.is_staff
        
        if not (is_owner or is_admin):
            return Response({"detail": "Not authorized to view this receipt."}, status=status.HTTP_403_FORBIDDEN)
            
        # --- 3. CHECK IF FILE EXISTS, SERVE IT ---
        if receipt.pdf_file:
            try:
                # Serve the existing file
                response = HttpResponse(receipt.pdf_file.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'inline; filename="{receipt.receipt_no}.pdf"'
                return response
            except FileNotFoundError:
                # File was deleted from storage, fall through to regenerate
                pass

        # --- 4. FALLBACK: Generate if missing ---
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
    # ... (no change)
    serializer_class = FeesReceiptSerializer
    permission_classes = [IsStudent] 
    def get_queryset(self):
        try:
            student_id = self.request.user.student.id
            return FeesReceipt.objects.filter(student_id=student_id).select_related(
                "student__user", "course", "batch"
            ).order_by("-date")
        except Exception:
            return FeesReceipt.objects.none()

# ... (rest of finance/views.py is unchanged) ...
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
    queryset = StockItem.objects.all()
    serializer_class = StockItemSerializer
    permission_classes = [IsStaffOrReadOnly]
    search_fields = ["name", "description"]
    filterset_fields = ["unit_of_measure"]
    
    @action(detail=True, methods=["get"])
    def transactions(self, request, pk=None):
        item = self.get_object()
        transactions = item.transactions.all()
        page = self.paginate_queryset(transactions)
        serializer = StockTransactionSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)


class StockTransactionViewSet(viewsets.ModelViewSet):
    queryset = StockTransaction.objects.select_related("item", "user")
    serializer_class = StockTransactionSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ["item", "user"]


class ReminderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Reminder.objects.select_related(
        "student__user", "course", "batch", "sent_by"
    ).all()
    serializer_class = ReminderSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ["status", "student", "course", "batch"]
    search_fields = ["student__user__first_name", "student__user__last_name", "message"]
    ordering_fields = ["-sent_at"]