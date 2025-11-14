"""
URL configuration for the 'students' app.

Implements a nested route for student measurements using
`rest_framework_nested`.
"""
from rest_framework_nested import routers
from .views import EnquiryViewSet, StudentViewSet, StudentMeasurementViewSet, HistoricalStudentViewSet

# Main router
router = routers.DefaultRouter()
router.register(r"enquiries", EnquiryViewSet, basename="enquiry")
router.register(r"students", StudentViewSet, basename="student")
router.register(r"history/students", HistoricalStudentViewSet, basename="student-history")

# Nested router for: /students/<student_pk>/measurements/
students_router = routers.NestedSimpleRouter(router, r'students', lookup='student')
students_router.register(r'measurements', StudentMeasurementViewSet, basename='student-measurements')

# Combine the URL patterns
urlpatterns = router.urls + students_router.urls