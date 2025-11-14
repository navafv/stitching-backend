"""
Main URL configuration for the API (v1).

Includes routes for authentication, health checks, documentation,
and all application-specific API endpoints.
"""

from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import health_check

urlpatterns = [
    # 1. Authentication (JWT)
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
    # 2. Health Check
    path("health/", health_check, name="health-check"),
    
    # 3. App-level URLs
    path("", include("accounts.urls")),
    path("", include("students.urls")),
    path("", include("courses.urls")),
    path("", include("certificates.urls")),
    path("", include("notifications.urls")),
    path("", include("messaging.urls")), 
    path("", include("events.urls")),
    
    path("attendance/", include("attendance.urls")),
    path("finance/", include("finance.urls")),
    
    # 4. API Documentation
    path("", include("api.schema")),
]