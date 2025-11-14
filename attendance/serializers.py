"""
Serializers for the 'attendance' app.

Handles the complex logic for creating and updating Attendance records
with their nested AttendanceEntry instances.
"""

from django.db import transaction
from rest_framework import serializers
from .models import Attendance, AttendanceEntry
from courses.models import Enrollment


class StudentAttendanceEntrySerializer(serializers.ModelSerializer):
    """
    A read-only serializer for a student viewing their *own*
    attendance history. It flattens related data for easy consumption.
    """
    date = serializers.ReadOnlyField(source="attendance.date")
    batch_code = serializers.ReadOnlyField(source="attendance.batch.code")
    course_title = serializers.ReadOnlyField(source="attendance.batch.course.title")

    class Meta:
        model = AttendanceEntry
        fields = ["id", "date", "batch_code", "course_title", "status"]


class AttendanceEntrySerializer(serializers.ModelSerializer):
    """
    Serializer for a single attendance entry.
    Used nested within the main AttendanceSerializer.
    """
    student_name = serializers.ReadOnlyField(source="student.user.get_full_name")

    class Meta:
        model = AttendanceEntry
        fields = ["id", "student", "student_name", "status"]
        read_only_fields = ["id"]


class AttendanceSerializer(serializers.ModelSerializer):
    """
    Serializer for an Attendance sheet and its nested entries.
    
    Handles the core business logic for:
    - Creating/updating an Attendance record and its entries in one transaction.
    - Validating that no duplicate students are in a payload.
    - Triggering a check for course completion for each student
      after attendance is saved.
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
        """Returns the calculated P/A/L summary from the model property."""
        return obj.summary()
    
    def _check_student_completion(self, batch, student_id):
        """
        Finds the student's active enrollment for this course and triggers
        a status check (Enrollment.check_and_update_status) to see if
        they have met the required attendance days.
        """
        try:
            # Find the student's *active* enrollment for this *course*.
            # Attendance is counted at the course level, not batch level.
            enrollments = Enrollment.objects.filter(
                student_id=student_id, 
                batch__course=batch.course,
                status="active"
            )
            for enrollment in enrollments:
                enrollment.check_and_update_status()
                
        except Enrollment.DoesNotExist:
            # No active enrollment found for this student/course.
            pass
        except Exception:
            # Fails silently if multiple enrollments or other issues,
            # to avoid blocking the attendance save.
            pass

    def _validate_student_ids(self, entries_data):
        """Ensures no duplicate students are in a single attendance payload."""
        student_ids = [e["student"].id for e in entries_data]
        if len(student_ids) != len(set(student_ids)):
            raise serializers.ValidationError(
                {"entries": "Duplicate student entries detected in this submission."}
            )
        return student_ids

    @transaction.atomic
    def create(self, validated_data):
        """
        Creates an Attendance record and its associated entries in a transaction.
        Checks for student completion status after creation.
        """
        entries_data = validated_data.pop("entries", [])
        student_ids = self._validate_student_ids(entries_data)
        
        # Create the parent Attendance record
        attendance = Attendance.objects.create(**validated_data)

        # Bulk create all nested AttendanceEntry records
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
        Updates an Attendance record and *replaces* its entries in a transaction.
        Checks for student completion status after update.
        """
        entries_data = validated_data.pop("entries", None)
        
        # Update parent Attendance instance fields (date, remarks, etc.)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        if entries_data is not None:
            # If 'entries' payload is part of the update,
            # delete old entries and bulk create new ones.
            student_ids = self._validate_student_ids(entries_data)

            instance.entries.all().delete()
            AttendanceEntry.objects.bulk_create([
                AttendanceEntry(attendance=instance, **e) for e in entries_data
            ])
            
            # After saving, check completion status for each student
            for student_id in student_ids:
                self._check_student_completion(instance.batch, student_id)
                
        return instance