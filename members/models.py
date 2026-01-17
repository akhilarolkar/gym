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
    phone_number = models.CharField(max_length=15, blank=True)
    join_date = models.DateField()
    membership_type = models.CharField(max_length=50)
    membership_start_date = models.DateField(default=timezone.now)
    membership_end_date = models.DateField()
    dob = models.DateField(blank=True, null=True, verbose_name="Date of Birth")
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], blank=True)
    is_active = models.BooleanField(default=True)
    fees_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Fees Amount")
    payment_mode = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('Cash', 'Cash'),
        ('Credit Card', 'Credit Card'),
        ('Debit Card', 'Debit Card'),
        ('UPI', 'UPI'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Other', 'Other'),
    ])
    transaction_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="Transaction ID")
    comments = models.TextField(blank=True, null=True, verbose_name="Comments")

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
