"""
Serializers for the 'certificates' app.
"""

from rest_framework import serializers
from .models import Certificate
from courses.models import Enrollment

class CertificateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating, validating, and displaying Certificates.
    
    Includes business logic to ensure certificates are only issued
    to students who have completed the course.
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
        read_only_fields = [
            "certificate_no", "issue_date", "qr_hash", "pdf_file", 
            "student_name", "course_title"
        ]

    def validate(self, attrs):
        """
        Business logic validation before issuing a certificate.
        1. Check if a non-revoked certificate already exists.
        2. Check if the student has a 'completed' enrollment for the course.
        """
        student = attrs.get("student")
        course = attrs.get("course")
        
        if not (student and course):
            # This validation only applies when creating/updating both fields
            return attrs

        # 1. CHECK FOR EXISTING CERTIFICATE
        existing_cert_query = Certificate.objects.filter(
            student=student, course=course, revoked=False
        )
        if self.instance:
            # If updating, exclude the current instance from the check
            existing_cert_query = existing_cert_query.exclude(id=self.instance.id)
        
        if existing_cert_query.exists():
            raise serializers.ValidationError(
                "A valid certificate already exists for this student and course."
            )
        
        # 2. CHECK FOR COURSE COMPLETION
        # Find at least one 'completed' enrollment for this student and course
        has_completed_enrollment = Enrollment.objects.filter(
            student=student, 
            batch__course=course,
            status="completed" # Must be marked as 'completed'
        ).exists()

        if not has_completed_enrollment:
            # If no completed enrollment, check for an active one to give a
            # more helpful error message.
            active_enrollment = Enrollment.objects.filter(
                student=student, batch__course=course, status="active"
            ).first()
            
            if active_enrollment:
                raise serializers.ValidationError(
                    f"Student has not completed this course. "
                    f"Attendance: {active_enrollment.get_present_days_count()}/"
                    f"{course.required_attendance_days} days."
                )
            else:
                 raise serializers.ValidationError(
                    "Student is not enrolled in this course or "
                    "no active/completed enrollment was found."
                 )

        return attrs