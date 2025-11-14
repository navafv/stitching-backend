"""
Main URL configuration for the API (v1).

Includes routes for:
1. Authentication (JWT token obtain/refresh)
2. A public health check endpoint
3. All application-specific API endpoints (from other apps)
4. API documentation endpoints
"""

from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import health_check

urlpatterns = [
    # 1. Authentication (JWT)
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # 2. Health Check (Public)
    path("health/", health_check, name="health-check"),

    # 3. App-level URLs
    path("", include("accounts.urls")),
    path("", include("students.urls")),
    path("", include("courses.urls")),
    path("", include("certificates.urls")),
    path("", include("notifications.urls")),
    path("", include("messaging.urls")),
    path("", include("events.urls")),

    # These apps are prefixed for clarity
    path("attendance/", include("attendance.urls")),
    path("finance/", include("finance.urls")),

    # 4. API Documentation (Handled by core.urls.py, but could be here)
    # path("", include("api.schema")),
]