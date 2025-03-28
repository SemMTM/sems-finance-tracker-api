from django.db import models
from django.contrib.auth.models import User
from .shared import REPEATED_CHOICES, TYPE


class Expenditure(models.Model):
    """
    Represents a spending entry outside disposable income (e.g., bills).
    """
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, blank=False)
    amount = models.PositiveIntegerField(blank=False)
    repeated = models.CharField(choices=REPEATED_CHOICES, default='NEVER')
    type = models.CharField(choices=TYPE, default='BILL')
    date = models.DateTimeField(blank=False)

    def __str__(self):
        return f"{self.owner} Expenditure: {self.title} - {self.amount}"
