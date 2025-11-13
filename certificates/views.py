from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
# --- 1. IMPORT IsStudent ---
from api.permissions import IsStaffOrReadOnly, IsAdmin, IsStudent
from rest_framework.permissions import AllowAny
from .models import Certificate
from .serializers import CertificateSerializer


class CertificateViewSet(viewsets.ModelViewSet):
    # ... (no change to this admin viewset)
    queryset = Certificate.objects.select_related("student__user", "course")
    serializer_class = CertificateSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ["revoked", "course", "student", "issue_date"]
    search_fields = ["certificate_no", "student__user__username", "student__reg_no"]
    ordering_fields = ["issue_date", "certificate_no"]

    # 🔍 Public endpoint for verification by QR hash
    @action(detail=False, methods=["get"], permission_classes=[AllowAny], url_path="verify/(?P<qr_hash>[^/.]+)")
    def verify_certificate(self, request, qr_hash=None):
        # ... (no change)
        """Public QR-based verification endpoint."""
        cert = Certificate.objects.filter(qr_hash=qr_hash, revoked=False).select_related("student__user", "course").first()
        if not cert:
            return Response({"valid": False, "message": "Certificate not found or revoked."}, status=status.HTTP_404_NOT_FOUND)
        data = {
            "valid": True,
            "certificate_no": cert.certificate_no,
            "student": cert.student.user.get_full_name(),
            "course": cert.course.title if cert.course else None,
            "issue_date": cert.issue_date,
            "remarks": cert.remarks,
        }
        return Response(data)


    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def revoke(self, request, pk=None):
        # ... (no change)
        """
        Toggles the revocation status of a certificate.
        """
        cert = self.get_object()
        new_status = not cert.revoked
        cert.revoked = new_status
        cert.save(update_fields=["revoked"])
        status_text = "revoked" if new_status else "un-revoked"
        return Response({"detail": f"Certificate has been {status_text}."})


# --- 2. ADD NEW VIEWSET FOR STUDENTS ---
class StudentCertificateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only endpoint for a student to view their *own* certificates.
    """
    serializer_class = CertificateSerializer
    permission_classes = [IsStudent] # Only students

    def get_queryset(self):
        """Filter certificates to only those owned by the logged-in student."""
        try:
            student_id = self.request.user.student.id
            return Certificate.objects.filter(
                student_id=student_id,
                revoked=False # Only show valid certificates
            ).select_related(
                "student__user", "course"
            ).order_by("-issue_date")
        except Exception:
            return Certificate.objects.none()