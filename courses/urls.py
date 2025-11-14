"""
URL configuration for the 'courses' app.

Registers standard ViewSets and a nested ViewSet for course materials
using `rest_framework_nested`.
"""
from rest_framework_nested import routers
from .views import (
    CourseViewSet, TrainerViewSet, BatchViewSet, 
    EnrollmentViewSet, BatchFeedbackViewSet,
    CourseMaterialViewSet, StudentMaterialsViewSet
)

router = routers.DefaultRouter()
router.register(r"courses", CourseViewSet, basename="course")
router.register(r"trainers", TrainerViewSet, basename="trainer")
router.register(r"batches", BatchViewSet, basename="batch")
router.register(r"enrollments", EnrollmentViewSet, basename="enrollment")
router.register(r"feedback", BatchFeedbackViewSet, basename="feedback")

# Student-facing endpoint for their materials
router.register(r"my-materials", StudentMaterialsViewSet, basename="my-materials")

# --- Nested Route for Admin ---
# Creates /api/v1/courses/<course_pk>/materials/
courses_router = routers.NestedSimpleRouter(router, r'courses', lookup='course')
courses_router.register(r'materials', CourseMaterialViewSet, basename='course-materials')

urlpatterns = router.urls + courses_router.urls