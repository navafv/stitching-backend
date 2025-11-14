"""
URL configuration for the 'certificates' app.
"""

from rest_framework.routers import DefaultRouter
from .views import CertificateViewSet, StudentCertificateViewSet

router = DefaultRouter()

# Endpoint for Admins to manage all certificates
# e.g., /api/v1/certificates/
router.register(r"certificates", CertificateViewSet, basename="certificate")

# Read-only endpoint for students to view their own certificates
# e.g., /api/v1/my-certificates/
router.register(r"my-certificates", StudentCertificateViewSet, basename="my-certificates")

urlpatterns = router.urls