from django.db import models
from django.contrib.auth.models import User


class DisposableIncomeBudget(models.Model):
    """
    Stores the user’s set budget for disposable spending.
    """
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(null=False, blank=False)

    def __str__(self):
        return f"{self.owner} Budget: {self.amount}"


class DisposableIncomeSpending(models.Model):
    """
    Tracks spending from the user's disposable income.
    """
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, blank=False)
    amount = models.PositiveIntegerField(blank=False)
    date = models.DateTimeField(blank=False)

    def __str__(self):
        return f"{self.owner} DIS: {self.title} - {self.amount}"
