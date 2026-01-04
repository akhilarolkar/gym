from django.db import models
from django.utils import timezone
from datetime import timedelta

class Member(models.Model):
    MEMBERSHIP_DURATIONS = {
        'strength': 30,  # days
        'cardio': 90,
        'crossfit': 365,
    }

    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    join_date = models.DateField()
    membership_type = models.CharField(max_length=50)
    membership_start_date = models.DateField(default=timezone.now)
    membership_end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def update_membership(self, new_type=None):
        if new_type:
            self.membership_type = new_type
        duration = self.MEMBERSHIP_DURATIONS.get(self.membership_type, 30)
        self.membership_end_date = self.membership_start_date + timedelta(days=duration)
        self.save()
