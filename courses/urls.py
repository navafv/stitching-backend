"""
UPDATED FILE: stitching-backend/courses/urls.py
Registered the new TeacherViewSet.
"""
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet, TrainerViewSet, BatchViewSet, 
    EnrollmentViewSet, BatchFeedbackViewSet
)

router = DefaultRouter()
router.register(r"courses", CourseViewSet, basename="course")
router.register(r"trainers", TrainerViewSet, basename="trainer")
router.register(r"batches", BatchViewSet, basename="batch")
router.register(r"enrollments", EnrollmentViewSet, basename="enrollment")
router.register(r"feedback", BatchFeedbackViewSet, basename="feedback")

urlpatterns = router.urls