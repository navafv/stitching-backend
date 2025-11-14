"""
Data models for the 'finance' app.

Defines all financial entities:
- FeesReceipt: Records a student's fee payment.
- Expense: Records an operational expense for the institute.
- Payroll: Records a salary payment to a Trainer.
- Reminder: Logs a fee reminder sent to a student.
- StockItem: Represents an inventory item (e.g., fabric, thread).
- StockTransaction: Logs changes to an inventory item's quantity.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from students.models import Student
from courses.models import Course, Batch, Trainer
from simple_history.models import HistoricalRecords
from django.db.models import Sum


class FeesReceipt(models.Model):
    """
    Represents a single fee payment received from a student.
    """
    MODE_CHOICES = [
        ("cash", "Cash"),
        ("upi", "UPI"),
        ("bank", "Bank Transfer"),
        ("card", "Card"),
    ]

    receipt_no = models.CharField(max_length=30, unique=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="receipts")
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    txn_id = models.CharField(max_length=50, blank=True)
    date = models.DateField(auto_now_add=True)
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    # 'locked' prevents editing or deletion via the admin or API
    locked = models.BooleanField(default=False)
    
    # Stores the auto-generated PDF receipt
    pdf_file = models.FileField(upload_to="finance/receipts/", blank=True, null=True)
    
    history = HistoricalRecords()

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [
            models.Index(fields=["receipt_no"]),
            models.Index(fields=["date"]),
            models.Index(fields=["mode"]),
            models.Index(fields=["locked"]),
        ]
        verbose_name = "Fees Receipt"
        verbose_name_plural = "Fees Receipts"

    def __str__(self):
        return f"Receipt {self.receipt_no} - {self.student}"

    @property
    def is_editable(self) -> bool:
        """Helper property to check if the receipt is mutable."""
        return not self.locked


class Expense(models.Model):
    """
    Represents an operational expense (e.g., materials, maintenance, salary).
    """
    CATEGORY_CHOICES = [
        ("material", "Material"),
        ("maintenance", "Maintenance"),
        ("salary", "Salary"), # Note: 'Payroll' model is preferred for trainer salaries
        ("other", "Other"),
    ]

    date = models.DateField(auto_now_add=True)
    description = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["category"]),
        ]
        verbose_name = "Expense"
        verbose_name_plural = "Expenses"

    def __str__(self):
        return f"{self.get_category_display()} - {self.amount}"


class Payroll(models.Model):
    """
    Represents a salary payment record for a Trainer for a specific month.
    """
    month = models.CharField(
        max_length=7,  # "YYYY-MM"
        validators=[RegexValidator(r"^\d{4}-(0[1-9]|1[0-2])$", "Month must be in YYYY-MM format.")],
        help_text='Format: "YYYY-MM"',
    )
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    earnings = models.JSONField(default=dict)
    deductions = models.JSONField(default=dict)
    net_pay = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        # Ensures one payroll record per trainer per month
        unique_together = ("trainer", "month")
        ordering = ["-month", "-id"]
        indexes = [
            models.Index(fields=["month"]),
            models.Index(fields=["status"]),
            models.Index(fields=["trainer"]),
        ]
        verbose_name = "Payroll"
        verbose_name_plural = "Payroll"

    def __str__(self):
        return f"Payroll for {self.trainer} - {self.month}"


class Reminder(models.Model):
    """
    Logs a fee reminder sent to a student.
    Can be created manually or by an automated job.
    """
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    class Meta:
        ordering = ["-sent_at"]
        verbose_name = "Fee Reminder"
        verbose_name_plural = "Fee Reminders"

    def __str__(self):
        return f"Reminder to {self.student} ({self.status})"


class StockItem(models.Model):
    """
    Represents an item in the inventory, like fabric, thread, buttons.
    """
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    unit_of_measure = models.CharField(max_length=20, help_text="e.g., 'meters', 'pieces', 'kg'")
    quantity_on_hand = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reorder_level = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Quantity at which to re-order"
    )
    
    class Meta:
        ordering = ["name"]
        verbose_name = "Stock Item"
        verbose_name_plural = "Stock Items"

    def __str__(self):
        return f"{self.name} ({self.quantity_on_hand} {self.unit_of_measure})"
    
    @property
    def needs_reorder(self) -> bool:
        """Returns True if quantity is at or below reorder level."""
        return self.quantity_on_hand <= self.reorder_level


class StockTransaction(models.Model):
    """
    Logs every change in stock quantity (e.g., purchase, usage, wastage).
    This model automatically updates the parent StockItem's quantity_on_hand
    via its save() and delete() methods.
    """
    item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name="transactions")
    date = models.DateTimeField(auto_now_add=True)
    quantity_changed = models.DecimalField(
        max_digits=10,
        decimal_places=2, 
        help_text="Positive for adding stock (e.g., purchase), negative for removing (e.g., usage)"
    )
    reason = models.CharField(
        max_length=255,
        blank=True,
        help_text="e.g., 'Purchase Order 123', 'Used for Batch BT-01', 'Wastage'"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ["-date"]
        verbose_name = "Stock Transaction"
        verbose_name_plural = "Stock Transactions"

    def __str__(self):
        return f"{self.item.name}: {self.quantity_changed:+} on {self.date.date()}"

    def save(self, *args, **kwargs):
        """
        Automatically update the StockItem's quantity_on_hand on create.
        """
        is_new = self._state.adding
        super().save(*args, **kwargs) # Save transaction first
        
        if is_new:
            # On create, update the parent item's stock level
            self.item.quantity_on_hand = (self.item.quantity_on_hand or 0) + self.quantity_changed
            self.item.save(update_fields=["quantity_on_hand"])
        # Note: Handling updates to quantity_changed is complex and generally
        # disallowed. A change should be a new, correcting transaction.

    def delete(self, *args, **kwargs):
        """
        On delete, reverse the quantity change from the parent item.
        (e.g., if a transaction was a mistake).
        """
        self.item.quantity_on_hand = (self.item.quantity_on_hand or 0) - self.quantity_changed
        self.item.save(update_fields=["quantity_on_hand"])
        super().delete(*args, **kwargs)