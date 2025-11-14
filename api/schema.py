"""
URL configuration for API schema and documentation endpoints.

Registers the `drf-spectacular` views for generating
OpenAPI schema and serving Swagger/Redoc UI.
"""

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from django.urls import path

urlpatterns = [
    # Endpoint to download the OpenAPI schema (schema.yml)
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    
    # Interactive API documentation UIs
    path("docs/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("docs/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]