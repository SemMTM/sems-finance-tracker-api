from django.db import models
from django.contrib.auth.models import User


REPEATED_CHOICES = [
        ('NEVER', 'Never'),
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
    ]

TYPE = [
    ('BILL', 'Bill'),
    ('SAVING', 'Savings'),
    ('INVESTMENT', 'Investment'),
]


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

    def __str__(self):
        return f"{self.owner} DIS: {self.title} - {self.amount}"


class Currency(models.Model):
    """
    Represents a user's selected currency preference.
    """
    CURRENCY_TYPE_CHOICES = [
        ('USD', 'US Dollar $'),
        ('EUR', 'Euro €'),
        ('JPY', 'Japanese Yen ¥'),
        ('GBP', 'British Pound £'),
        ('AUD', 'Australian Dollar A$'),
        ('CAD', 'Canadian Dollar C$'),
        ('CHF', 'Swiss Franc CHF'),
        ('CNY', 'Chinese Yuan ¥'),
        ('HKD', 'Hong Kong Dollar HK$'),
        ('INR', 'Indian Rupee ₹'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    currency = models.CharField(
        choices=CURRENCY_TYPE_CHOICES, default="GBP")

    def __str__(self):
        return f"{self.owner.username}'s Currency: {self.currency}"
