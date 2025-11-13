"""
Attendance Serializers
----------------------
Enhancements:
- Added atomic creation and update of entries.
- Added validation for duplicate students and batch mismatch.
- Returns summary info and readable labels.
"""

from django.db import transaction
from rest_framework import serializers
from .models import Attendance, AttendanceEntry
from courses.models import Enrollment


class StudentAttendanceEntrySerializer(serializers.ModelSerializer):
    """
    Read-only serializer for a student to view their own attendance.
    """
    date = serializers.ReadOnlyField(source="attendance.date")
    batch_code = serializers.ReadOnlyField(source="attendance.batch.code")
    course_title = serializers.ReadOnlyField(source="attendance.batch.course.title")

    class Meta:
        model = AttendanceEntry
        fields = ["id", "date", "batch_code", "course_title", "status"]


class AttendanceEntrySerializer(serializers.ModelSerializer):
    """Serializer for individual student attendance entry."""
    student_name = serializers.ReadOnlyField(source="student.user.get_full_name")

    class Meta:
        model = AttendanceEntry
        fields = ["id", "student", "student_name", "status"]
        read_only_fields = ["id"]

    def validate_status(self, value):
        if value not in dict(AttendanceEntry.STATUS_CHOICES):
            raise serializers.ValidationError("Invalid status code. Must be P, A, or L.")
        return value


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer for Attendance with nested entries."""
    entries = AttendanceEntrySerializer(many=True)
    batch_code = serializers.ReadOnlyField(source="batch.code")
    summary = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Attendance
        fields = [
            "id", "batch", "batch_code", "date", "taken_by", "remarks",
            "entries", "summary",
        ]
        read_only_fields = ["id", "summary"]

    def get_summary(self, obj):
        """Returns attendance summary breakdown."""
        return obj.summary()
    
    def _check_student_completion(self, batch, student_id):
        """Finds the student's enrollment and checks their status."""
        try:
            enrollment = Enrollment.objects.get(
                student_id=student_id, 
                batch__course=batch.course
            )
            enrollment.check_and_update_status()
        except Enrollment.DoesNotExist:
            # Student might be in this batch but enrolled in a different course?
            # Or just no enrollment. Safe to ignore.
            pass
        except Enrollment.MultipleObjectsReturned:
            # This shouldn't happen with the unique_together, but just in case
            enrollments = Enrollment.objects.filter(
                student_id=student_id, 
                batch__course=batch.course
            )
            for enrollment in enrollments:
                enrollment.check_and_update_status()

    @transaction.atomic
    def create(self, validated_data):
        """Safely creates attendance with entries."""
        entries_data = validated_data.pop("entries", [])
        attendance = Attendance.objects.create(**validated_data)
        
        student_ids = [e["student"].id for e in entries_data]
        if len(student_ids) != len(set(student_ids)):
            raise serializers.ValidationError("Duplicate student entries detected.")

        AttendanceEntry.objects.bulk_create([
            AttendanceEntry(attendance=attendance, **e) for e in entries_data
        ])
        
        for student_id in student_ids:
            self._check_student_completion(attendance.batch, student_id)
            
        return attendance

    @transaction.atomic
    def update(self, instance, validated_data):
        """Safely replaces or updates attendance entries."""
        entries_data = validated_data.pop("entries", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        if entries_data is not None:
            student_ids = [e["student"].id for e in entries_data]
            if len(student_ids) != len(set(student_ids)):
                raise serializers.ValidationError("Duplicate student entries detected.")

            # simple approach: replace all entries
            instance.entries.all().delete()
            AttendanceEntry.objects.bulk_create([
                AttendanceEntry(attendance=instance, **e) for e in entries_data
            ])
            
            for student_id in student_ids:
                self._check_student_completion(instance.batch, student_id)
                
        return instance
