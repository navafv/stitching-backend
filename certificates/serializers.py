from rest_framework import serializers
from .models import Certificate

class CertificateSerializer(serializers.ModelSerializer):
    student_name = serializers.ReadOnlyField(source="student.user.get_full_name")
    course_title = serializers.ReadOnlyField(source="course.title")

    class Meta:
        model = Certificate
        fields = [
            "id", "certificate_no", "student", "student_name",
            "course", "course_title", "issue_date", "qr_hash",
            "remarks", "revoked", "pdf_file"
        ]
        read_only_fields = ["certificate_no", "issue_date", "qr_hash", "pdf_file"]

    def validate(self, attrs):
        student = attrs.get("student")
        course = attrs.get("course")
        if student and course:
            existing = Certificate.objects.filter(student=student, course=course, revoked=False)
            if self.instance:
                existing = existing.exclude(id=self.instance.id)
            if existing.exists():
                raise serializers.ValidationError(
                    "Certificate already issued for this student and course."
                )
        return attrs
