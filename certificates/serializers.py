"""
Serializers for the 'certificates' app.
"""

from rest_framework import serializers
from .models import Certificate
from courses.models import Enrollment

class CertificateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating, validating, and displaying Certificates.
    """
    student_name = serializers.ReadOnlyField(source="student.user.get_full_name")
    course_title = serializers.ReadOnlyField(source="course.title")

    class Meta:
        model = Certificate
        fields = [
            "id", "certificate_no", "student", "student_name",
            "course", "course_title", "issue_date", "qr_hash",
            "remarks", "revoked", "pdf_file"
        ]
        read_only_fields = ["certificate_no", "issue_date", "qr_hash", "pdf_file", "student_name", "course_title"]

    def validate(self, attrs):
        """
        Business logic validation before issuing a certificate.
        1. Check if a non-revoked certificate already exists.
        2. Check if the student has actually completed the course.
        """
        student = attrs.get("student")
        course = attrs.get("course")
        
        if not (student and course):
            # This validation only applies when both are being set
            return attrs

        # 1. CHECK FOR EXISTING CERTIFICATE
        existing_cert = Certificate.objects.filter(student=student, course=course, revoked=False)
        if self.instance:
            # If updating, exclude the current instance from the check
            existing_cert = existing_cert.exclude(id=self.instance.id)
        
        if existing_cert.exists():
            raise serializers.ValidationError(
                "A valid certificate already exists for this student and course."
            )
        
        # 2. CHECK FOR COURSE COMPLETION
        try:
            # Find a completed enrollment for this student and course
            enrollment = Enrollment.objects.get(
                student=student, 
                batch__course=course,
                status="completed" # Must be marked as completed
            )
        except Enrollment.DoesNotExist:
            # If no *completed* enrollment, check active ones for completion status
            try:
                active_enrollment = Enrollment.objects.get(student=student, batch__course=course, status="active")
                raise serializers.ValidationError(
                    f"Student has not completed this course. "
                    f"Attendance: {active_enrollment.get_present_days_count()}/{course.required_attendance_days} days."
                )
            except Enrollment.DoesNotExist:
                 raise serializers.ValidationError("Student is not enrolled in this course.")
            except Enrollment.MultipleObjectsReturned:
                # This case is complex, but if they have no *completed* one, deny.
                 raise serializers.ValidationError("Student has multiple active/dropped enrollments but none are 'completed'.")

        except Enrollment.MultipleObjectsReturned:
            # This means they have multiple *completed* enrollments. This is fine.
            pass

        return attrs