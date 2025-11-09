from django.contrib import admin
from .models import Certificate

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_no', 'student', 'course', 'issue_date', 'revoked')
    list_filter = ('revoked', 'issue_date')
    search_fields = ('certificate_no', 'student__user__username', 'course__title')
    readonly_fields = ('qr_hash', 'issue_date')
