from django.db import models
from django.contrib.auth.models import User
from .shared import REPEATED_CHOICES


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
