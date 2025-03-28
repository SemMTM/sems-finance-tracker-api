from django.db import models
from django.contrib.auth.models import User


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
