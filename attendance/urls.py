from rest_framework.routers import DefaultRouter
from .views import AttendanceViewSet, StudentAttendanceViewSet
from .views_analytics import AttendanceAnalyticsViewSet

router = DefaultRouter()
router.register("records", AttendanceViewSet, basename="attendance")
router.register("analytics", AttendanceAnalyticsViewSet, basename="attendance-analytics")
router.register("my-history", StudentAttendanceViewSet, basename="my-attendance-history")

urlpatterns = router.urls
