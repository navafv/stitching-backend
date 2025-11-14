"""
Views for the 'certificates' app.

Provides API endpoints for:
- Admin management of certificates (CRUD).
- Public verification of certificates via QR hash.
- Secure downloading of PDF certificates by owners or admins.
- Student-specific endpoint to view their own certificates.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated 
from api.permissions import IsStaffOrReadOnly, IsAdmin, IsStudent
from .models import Certificate
from .serializers import CertificateSerializer
from django.http import HttpResponse, FileResponse
from django.shortcuts import get_object_or_404
import logging

logger = logging.getLogger(__name__)


class CertificateViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Admin management of certificates.
    """
    queryset = Certificate.objects.select_related("student__user", "course").order_by("-issue_date")
    serializer_class = CertificateSerializer
    permission_classes = [IsAdmin] # Only Admins can manage certificates
    filterset_fields = ["revoked", "course", "student", "issue_date"]
    search_fields = ["certificate_no", "student__user__username", "student__reg_no", "course__title"]
    ordering_fields = ["issue_date", "certificate_no"]

    @action(detail=False, methods=["get"], permission_classes=[AllowAny], url_path="verify/(?P<qr_hash>[^/.]+)")
    def verify_certificate(self, request, qr_hash=None):
        """
        Public endpoint to verify a certificate's validity using its unique hash.
        """
        try:
            cert = Certificate.objects.select_related(
                "student__user", "course"
            ).get(qr_hash=qr_hash, revoked=False)
        except Certificate.DoesNotExist:
             return Response({"valid": False, "message": "Certificate not found or revoked."}, status=status.HTTP_404_NOT_FOUND)

        data = {
            "valid": True,
            "certificate_no": cert.certificate_no,
            "student_name": cert.student.user.get_full_name(),
            "course_title": cert.course.title if cert.course else None,
            "issue_date": cert.issue_date,
            "remarks": cert.remarks,
        }
        return Response(data)


    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def revoke(self, request, pk=None):
        """
        Toggles the 'revoked' status of a certificate.
        """
        cert = self.get_object()
        new_status = not cert.revoked
        cert.revoked = new_status
        cert.save(update_fields=["revoked"])
        
        status_text = "revoked" if new_status else "un-revoked"
        logger.info(f"Admin user {request.user.username} {status_text} certificate {cert.certificate_no}")
        
        return Response({"detail": f"Certificate has been {status_text}.", "revoked": new_status})

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated]) 
    def download(self, request, pk=None):
        """
        Securely downloads the certificate PDF.
        Accessible by Admins OR the student who owns it.
        """
        cert = get_object_or_404(Certificate, pk=pk)

        # Permission check
        is_owner = request.user == cert.student.user
        is_admin = request.user.is_staff
        
        if not (is_owner or is_admin):
            return Response({"detail": "Not authorized to download this file."}, status=status.HTTP_403_FORBIDDEN)
            
        if not cert.pdf_file:
            return Response({"detail": "PDF file not found for this certificate."}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Stream the file response
            return FileResponse(
                cert.pdf_file.open('rb'), 
                as_attachment=True, 
                filename=cert.pdf_file.name.split('/')[-1]
            )
        except FileNotFoundError:
            logger.warning(f"Certificate PDF file not found on storage: {cert.pdf_file.name}")
            return Response({"detail": "File not found on server."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error accessing certificate file {cert.pdf_file.name}: {e}")
            return Response({"detail": f"Error accessing file: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StudentCertificateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only endpoint for students to retrieve their own valid certificates.
    """
    serializer_class = CertificateSerializer
    permission_classes = [IsStudent]

    def get_queryset(self):
        """Filters certificates for the authenticated student."""
        try:
            student_id = self.request.user.student.id
            return Certificate.objects.filter(
                student_id=student_id,
                revoked=False
            ).select_related(
                "student__user", "course"
            ).order_by("-issue_date")
        except Student.DoesNotExist:
            return Certificate.objects.none()
        except Exception:
            return Certificate.objects.none()