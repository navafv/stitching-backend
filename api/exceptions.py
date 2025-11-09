# api/exceptions.py
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    resp = drf_exception_handler(exc, context)
    if resp is not None:
        # normalize DRF errors
        return resp
    # unhandled exception -> log and return generic error
    logger.exception("Unhandled API error", exc_info=exc)
    return Response({"detail": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
