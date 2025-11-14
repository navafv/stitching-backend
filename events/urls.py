"""
URL configuration for the 'events' app.
"""

from rest_framework.routers import DefaultRouter
from .views import EventViewSet

router = DefaultRouter()

# Registers /api/v1/events/
router.register(r"events", EventViewSet, basename="event")

urlpatterns = router.urls