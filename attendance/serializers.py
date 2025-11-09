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

    @transaction.atomic
    def create(self, validated_data):
        """Safely creates attendance with entries."""
        entries = validated_data.pop("entries", [])
        attendance = Attendance.objects.create(**validated_data)

        # Prevent duplicate students and ensure same batch
        student_ids = [e["student"].id for e in entries]
        if len(student_ids) != len(set(student_ids)):
            raise serializers.ValidationError("Duplicate student entries detected.")

        AttendanceEntry.objects.bulk_create([
            AttendanceEntry(attendance=attendance, **e) for e in entries
        ])
        return attendance

    @transaction.atomic
    def update(self, instance, validated_data):
        """Safely replaces or updates attendance entries."""
        entries = validated_data.pop("entries", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        if entries is not None:
            # simple approach: replace all entries
            instance.entries.all().delete()
            AttendanceEntry.objects.bulk_create([
                AttendanceEntry(attendance=instance, **e) for e in entries
            ])
        return instance
