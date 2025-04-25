from django.db import models
from django.contrib.auth.models import User
from .shared import REPEATED_CHOICES
from core.utils.date_helpers import get_user_and_month_range
from datetime import timedelta


class Income(models.Model):
    """
    Represents an income source for the user.
    """
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, blank=False)
    amount = models.PositiveIntegerField(blank=False)
    date = models.DateTimeField(blank=False)
    repeated = models.CharField(choices=REPEATED_CHOICES, default='NEVER')

    def __str__(self):
        return f"{self.owner} Income: {self.title} - {self.amount}"

    def repeat_income(self, month_start_date, month_end_date):
        """
        Generate repeated income entries based on the repetition frequency.
        """
        if self.repeated == 'DAILY':
            self._repeat_daily(month_start_date, month_end_date)
        elif self.repeated == 'WEEKLY':
            self._repeat_weekly(month_start_date, month_end_date)
        elif self.repeated == 'MONTHLY':
            self._repeat_monthly(month_start_date, month_end_date)