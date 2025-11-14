"""
Serializers for the 'attendance' app.

Handles the creation and updating of Attendance records, including
nested AttendanceEntry instances, with transactional integrity.
"""

from django.db import transaction
from rest_framework import serializers
from .models import Attendance, AttendanceEntry
from courses.models import Enrollment


class StudentAttendanceEntrySerializer(serializers.ModelSerializer):
    """
    Read-only serializer for a student viewing their own attendance history.
    Flattens related data for easy consumption.
    """
    date = serializers.ReadOnlyField(source="attendance.date")
    batch_code = serializers.ReadOnlyField(source="attendance.batch.code")
    course_title = serializers.ReadOnlyField(source="attendance.batch.course.title")

    class Meta:
        model = AttendanceEntry
        fields = ["id", "date", "batch_code", "course_title", "status"]


class AttendanceEntrySerializer(serializers.ModelSerializer):
    """Serializer for a single attendance entry, used nested within AttendanceSerializer."""
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
    """
    Serializer for creating and managing an Attendance sheet with its nested entries.
    """
    entries = AttendanceEntrySerializer(many=True)
    batch_code = serializers.ReadOnlyField(source="batch.code")
    summary = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Attendance
        fields = [
            "id", "batch", "batch_code", "date", "taken_by", "remarks",
            "entries", "summary",
        ]
        read_only_fields = ["id", "summary", "batch_code"]

    def get_summary(self, obj):
        """Returns the calculated P/A/L summary from the model."""
        return obj.summary()
    
    def _check_student_completion(self, batch, student_id):
        """
        Finds the student's enrollment for this course and triggers
        a status check to see if they have met completion requirements.
        """
        try:
            # Find enrollment based on course, not specific batch,
            # as attendance is counted cross-batch for the same course.
            enrollment = Enrollment.objects.get(
                student_id=student_id, 
                batch__course=batch.course,
                status="active" # Only check active enrollments
            )
            enrollment.check_and_update_status()
        except Enrollment.DoesNotExist:
            # No active enrollment found for this student/course.
            pass
        except Enrollment.MultipleObjectsReturned:
            # Handle rare case of multiple active enrollments in the same course.
            enrollments = Enrollment.objects.filter(
                student_id=student_id, 
                batch__course=batch.course,
                status="active"
            )
            for enrollment in enrollments:
                enrollment.check_and_update_status()

    def _validate_student_ids(self, entries_data):
        """Ensures no duplicate students are in a single attendance payload."""
        student_ids = [e["student"].id for e in entries_data]
        if len(student_ids) != len(set(student_ids)):
            raise serializers.ValidationError({"entries": "Duplicate student entries detected."})
        return student_ids

    @transaction.atomic
    def create(self, validated_data):
        """
        Creates an Attendance record and its associated entries in a transaction.
        Checks for student completion status after creation.
        """
        entries_data = validated_data.pop("entries", [])
        student_ids = self._validate_student_ids(entries_data)
        
        attendance = Attendance.objects.create(**validated_data)

        AttendanceEntry.objects.bulk_create([
            AttendanceEntry(attendance=attendance, **e) for e in entries_data
        ])
        
        # After saving, check completion status for each student
        for student_id in student_ids:
            self._check_student_completion(attendance.batch, student_id)
            
        return attendance

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Updates an Attendance record and replaces its entries in a transaction.
        Checks for student completion status after update.
        """
        entries_data = validated_data.pop("entries", None)
        
        # Update parent Attendance instance
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        if entries_data is not None:
            # If entries are provided, replace them
            student_ids = self._validate_student_ids(entries_data)

            instance.entries.all().delete()
            AttendanceEntry.objects.bulk_create([
                AttendanceEntry(attendance=instance, **e) for e in entries_data
            ])
            
            # After saving, check completion status for each student
            for student_id in student_ids:
                self._check_student_completion(instance.batch, student_id)
                
        return instance