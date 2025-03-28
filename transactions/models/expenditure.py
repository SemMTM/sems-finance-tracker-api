from django.db import models
from django.contrib.auth.models import User
from .shared import REPEATED_CHOICES, TYPE


class Expenditure(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    amount = models.PositiveIntegerField()
    repeated = models.CharField(choices=REPEATED_CHOICES, default='NEVER')
    type = models.CharField(choices=TYPE, default='BILL')
    date = models.DateTimeField()

    def __str__(self):
        return f"{self.owner} Expenditure: {self.title} - {self.amount}"
