"""
Main URL configuration for the Django project.

Includes routes for the admin site, the main API (v1),
and API documentation endpoints (Swagger/Redoc).
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)

urlpatterns = [
    # Django Admin site
    path("admin/", admin.site.urls),

    # Main application API
    path("api/v1/", include("api.urls")),

    # --- API Documentation ---
    # Endpoint to generate the OpenAPI schema (schema.yml)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Swagger UI
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # Redoc UI
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)