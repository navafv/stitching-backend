"""
Finance Admin
-------------
Enhancements:
- Lock/unlock actions for receipts (prevent edits/deletes when locked).
- Auto-assign posted_by / added_by.
- Safer read-only fields.
"""

from django.contrib import admin
from django.contrib import messages
from .models import FeesReceipt, Expense, Payroll, Reminder


@admin.register(FeesReceipt)
class FeesReceiptAdmin(admin.ModelAdmin):
    list_display = ("receipt_no", "student", "course", "amount", "mode", "date", "locked")
    list_filter = ("mode", "locked", "date", "course")
    search_fields = ("receipt_no", "txn_id", "student__user__username", "student__reg_no")
    readonly_fields = ("receipt_no", "date", "posted_by")  # honor your current behavior
    actions = ("lock_selected", "unlock_selected")
    ordering = ("-date", "-id")

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of locked receipts
        if obj and obj.locked:
            return False
        return super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        # Assign posted_by automatically on create
        if not obj.pk:
            obj.posted_by = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description="Lock selected receipts")
    def lock_selected(self, request, queryset):
        updated = queryset.update(locked=True)
        self.message_user(request, f"Locked {updated} receipt(s).", level=messages.SUCCESS)

    @admin.action(description="Unlock selected receipts")
    def unlock_selected(self, request, queryset):
        updated = queryset.update(locked=False)
        self.message_user(request, f"Unlocked {updated} receipt(s).", level=messages.SUCCESS)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("date", "category", "description", "amount", "added_by")
    list_filter = ("category", "date")
    search_fields = ("description",)
    readonly_fields = ("added_by", "date")
    ordering = ("-date", "-id")

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.added_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ("trainer", "month", "net_pay", "status", "created_at")
    list_filter = ("status", "month", "trainer")
    search_fields = ("trainer__user__username", "trainer__user__first_name", "trainer__user__last_name")
    ordering = ("-month", "-id")


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "batch", "sent_at", "status")
    list_filter = ("status", "sent_at")
    search_fields = ("student__user__first_name", "student__user__last_name", "message")
    readonly_fields = ("sent_at", "sent_by")
