from rest_framework.routers import DefaultRouter
from .views import EnquiryViewSet, StudentViewSet

router = DefaultRouter()
router.register("enquiries", EnquiryViewSet, basename="enquiry")
router.register("students", StudentViewSet, basename="student")

urlpatterns = router.urls
