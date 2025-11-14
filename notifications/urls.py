"""
URL configuration for the 'notifications' app.
"""
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet

router = DefaultRouter()

# Registers /api/v1/notifications/
# Includes the /api/v1/notifications/send-bulk/ custom action
router.register(r"notifications", NotificationViewSet, basename="notification")

urlpatterns = router.urls