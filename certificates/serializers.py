from rest_framework import serializers
from .models import Certificate
from courses.models import Enrollment

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
            # CHECK FOR EXISTING CERTIFICATE
            existing = Certificate.objects.filter(student=student, course=course, revoked=False)
            if self.instance:
                existing = existing.exclude(id=self.instance.id)
            if existing.exists():
                raise serializers.ValidationError(
                    "Certificate already issued for this student and course."
                )
            
            # NEW COMPLETION CHECK
            try:
                enrollment = Enrollment.objects.get(student=student, batch__course=course)
                if enrollment.status != "completed":
                    raise serializers.ValidationError(
                        f"Student has not completed this course. "
                        f"Attendance: {enrollment.get_present_days_count()}/{course.required_attendance_days}"
                    )
            except Enrollment.DoesNotExist:
                raise serializers.ValidationError("Student is not enrolled in this course.")
            except Enrollment.MultipleObjectsReturned:
                # Handle if student enrolled multiple times (e.g., dropped and re-enrolled)
                # We just need one completed enrollment
                if not Enrollment.objects.filter(student=student, batch__course=course, status="completed").exists():
                     raise serializers.ValidationError(
                        "Student has multiple enrollments for this course, but none are marked 'completed'."
                    )

        return attrs