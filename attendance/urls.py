from rest_framework.routers import DefaultRouter
from .views import AttendanceViewSet
from .views_analytics import AttendanceAnalyticsViewSet

router = DefaultRouter()
router.register("records", AttendanceViewSet, basename="attendance")
router.register("analytics", AttendanceAnalyticsViewSet, basename="attendance-analytics")

urlpatterns = router.urls
