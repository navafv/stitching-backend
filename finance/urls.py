from rest_framework.routers import DefaultRouter
from .views import FeesReceiptViewSet, ExpenseViewSet, PayrollViewSet
from .views_analytics import FinanceAnalyticsViewSet
from .views_outstanding import OutstandingFeesViewSet

router = DefaultRouter()
router.register("receipts", FeesReceiptViewSet, basename="fees-receipt")
router.register("expenses", ExpenseViewSet, basename="expense")
router.register("payroll", PayrollViewSet, basename="payroll")
router.register("analytics", FinanceAnalyticsViewSet, basename="finance-analytics")
router.register("outstanding", OutstandingFeesViewSet, basename="finance-outstanding")

urlpatterns = router.urls
