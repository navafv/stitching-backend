from rest_framework.routers import DefaultRouter
from .views import EnquiryViewSet, StudentViewSet, StudentMeasurementViewSet

router = DefaultRouter()
router.register("enquiries", EnquiryViewSet, basename="enquiry")
router.register("students", StudentViewSet, basename="student")
router.register("measurements", StudentMeasurementViewSet, basename="measurement")

urlpatterns = router.urls
