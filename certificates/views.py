from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from api.permissions import IsStaffOrReadOnly
from rest_framework.permissions import AllowAny
from .models import Certificate
from .serializers import CertificateSerializer


class CertificateViewSet(viewsets.ModelViewSet):
    queryset = Certificate.objects.select_related("student__user", "course")
    serializer_class = CertificateSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ["revoked", "course", "student", "issue_date"]
    search_fields = ["certificate_no", "student__user__username", "student__reg_no"]
    ordering_fields = ["issue_date", "certificate_no"]

    # 🔍 Public endpoint for verification by QR hash
    @action(detail=False, methods=["get"], permission_classes=[AllowAny], url_path="verify/(?P<qr_hash>[^/.]+)")
    def verify_certificate(self, request, qr_hash=None):
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
