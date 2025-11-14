"""
URL configuration for the 'finance' app.

Registers all finance-related ViewSets, including core models,
analytics, and outstanding fee calculators.
"""

from rest_framework.routers import DefaultRouter
from .views import (
    FeesReceiptViewSet, ExpenseViewSet, PayrollViewSet, 
    StockItemViewSet, StockTransactionViewSet, ReminderViewSet,
    StudentReceiptsViewSet
)
from .views_analytics import FinanceAnalyticsViewSet
from .views_outstanding import OutstandingFeesViewSet

router = DefaultRouter()

# Core models
router.register("receipts", FeesReceiptViewSet, basename="fees-receipt")
router.register("expenses", ExpenseViewSet, basename="expense")
router.register("payroll", PayrollViewSet, basename="payroll")
router.register("stock-items", StockItemViewSet, basename="stock-item")
router.register("stock-transactions", StockTransactionViewSet, basename="stock-transaction")
router.register("reminders", ReminderViewSet, basename="reminder")

# Student-facing
router.register("my-receipts", StudentReceiptsViewSet, basename="my-receipts")

# Analytics & Reports
router.register("analytics", FinanceAnalyticsViewSet, basename="finance-analytics")
router.register("outstanding", OutstandingFeesViewSet, basename="finance-outstanding")

urlpatterns = router.urls