"""
Data models for the 'events' app.
"""

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class Event(models.Model):
    """
    Represents an institute-wide event, such as a holiday,
    a special workshop, or an announcement.
    
    These are typically managed by admins and displayed to all users.
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(
        null=True, 
        blank=True, 
        help_text="Leave blank for single-day events."
    )
    
    # Tracks which admin created the event
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_date'] # Show upcoming events first
        verbose_name = "Event"
        verbose_name_plural = "Events"

    def __str__(self):
        return self.title

    def clean(self):
        """
        Model-level validation to ensure the end_date
        is not before the start_date.
        """
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be before the start date.")
        
    def save(self, *args, **kwargs):
        """
        Overrides save to ensure clean() is called and to set
        end_date equal to start_date if it's a single-day event.
        """
        if self.end_date is None:
            self.end_date = self.start_date
        self.clean()
        super().save(*args, **kwargs)