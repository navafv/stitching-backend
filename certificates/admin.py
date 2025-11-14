"""
Admin configuration for the 'certificates' app.
"""

from django.contrib import admin
from .models import Certificate

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    """Admin interface customization for the Certificate model."""
    list_display = ('certificate_no', 'student', 'course', 'issue_date', 'revoked')
    list_filter = ('revoked', 'issue_date', 'course')
    search_fields = ('certificate_no', 'student__user__username', 'student__reg_no', 'course__title')
    
    # These fields are auto-generated, so they should not be editable.
    readonly_fields = ('certificate_no', 'qr_hash', 'issue_date', 'pdf_file')
    
    # Use dropdowns with search for foreign keys
    autocomplete_fields = ('student', 'course')