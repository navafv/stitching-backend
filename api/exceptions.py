"""
Custom exception handling for the API.

Ensures that all exceptions, including unhandled 500 errors,
return a standardized JSON error response instead of HTML.
"""

from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Handle all API exceptions, logging unhandled ones.
    """
    # Let DRF handle its own known exceptions first (e.g., ValidationError)
    resp = drf_exception_handler(exc, context)

    if resp is not None:
        # Use DRF's default formatted response
        return resp

    # For unhandled exceptions, log the full error and return a generic 500
    logger.exception(f"Unhandled API error in view {context['view'].__class__.__name__}", exc_info=exc)

    return Response(
        {"detail": "An unexpected internal server error occurred."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )