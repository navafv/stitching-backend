"""
URL configuration for the 'attendance' app.

Registers ViewSets for:
- `records`: Staff CRUD for daily attendance.
- `analytics`: Staff-facing analytics endpoints.
- `my-history`: Student-facing view of their own attendance.
"""

from rest_framework.routers import DefaultRouter
from .views import AttendanceViewSet, StudentAttendanceViewSet
from .views_analytics import AttendanceAnalyticsViewSet

router = DefaultRouter()
router.register("records", AttendanceViewSet, basename="attendance")
router.register("analytics", AttendanceAnalyticsViewSet, basename="attendance-analytics")
router.register("my-history", StudentAttendanceViewSet, basename="my-attendance-history")

urlpatterns = router.urls