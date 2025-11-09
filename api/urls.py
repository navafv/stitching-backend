from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import health_check

# Import all viewsets
from accounts.views import RoleViewSet, UserViewSet
from students.views import EnquiryViewSet, StudentViewSet
from courses.views import CourseViewSet, TrainerViewSet, BatchViewSet, EnrollmentViewSet
from finance.views import FeesReceiptViewSet, ExpenseViewSet, PayrollViewSet
from finance.views_analytics import FinanceAnalyticsViewSet
from finance.views_outstanding import OutstandingFeesViewSet
from attendance.views import AttendanceViewSet
from certificates.views import CertificateViewSet
from notifications.views import NotificationViewSet

# Initialize router
router = DefaultRouter()
router.register("roles", RoleViewSet)
router.register("users", UserViewSet)
router.register("enquiries", EnquiryViewSet)
router.register("students", StudentViewSet)
router.register("courses", CourseViewSet)
router.register("trainers", TrainerViewSet)
router.register("batches", BatchViewSet)
router.register("enrollments", EnrollmentViewSet)
router.register("fees/receipts", FeesReceiptViewSet)
router.register("expenses", ExpenseViewSet)
router.register("payroll", PayrollViewSet)
router.register("attendance", AttendanceViewSet)
router.register("certificates", CertificateViewSet)
router.register("finance/analytics", FinanceAnalyticsViewSet, basename="finance-analytics")
router.register("finance/outstanding", OutstandingFeesViewSet, basename="finance-outstanding")
router.register("notifications", NotificationViewSet, basename="notification")

# Main API patterns
urlpatterns = [
    # JWT Authentication
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Core routes
    path("", include(router.urls)),

    # API documentation
    path("", include("api.schema")),
    path("health/", health_check, name="health-check"),

]
