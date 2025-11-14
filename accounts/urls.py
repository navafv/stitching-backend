"""
URL configuration for the 'accounts' app.

Registers ViewSets for Roles, Users, and User History,
and adds custom paths for password reset functionality.
"""

from rest_framework.routers import DefaultRouter
from .views import (
    RoleViewSet, UserViewSet, HistoricalUserViewSet,
    ForgotPasswordView, ResetPasswordView
)
from django.urls import path

router = DefaultRouter()
router.register("roles", RoleViewSet, basename="role")
router.register("users", UserViewSet, basename="user")
router.register("history/users", HistoricalUserViewSet, basename="user-history")

# Combine router URLs with custom paths for password management
urlpatterns = router.urls + [
    path("auth/password-reset/", ForgotPasswordView.as_view(), name="password-reset-request"),
    path("auth/password-reset-confirm/", ResetPasswordView.as_view(), name="password-reset-confirm"),
]