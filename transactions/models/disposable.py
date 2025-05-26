from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator


class DisposableIncomeBudget(models.Model):
    """
    Represents the user’s monthly disposable income budget.
    Only one entry is allowed per user per month.
    """
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="disposable_income_budgets"
    )
    amount = models.PositiveIntegerField(
        default=0,
        blank=False,
        validators=[MaxValueValidator(1_000_000)],
        help_text="Budget amount in pence."
    )
    date = models.DateTimeField(
        blank=False,
        help_text="First day of the month this budget applies to."
    )

    class Meta:
        unique_together = ('owner', 'date')
        ordering = ['-date']
        verbose_name = "Disposable Income Budget"

    def __str__(self) -> str:
        return f"{
            self.owner.username}'s Budget for  {self.date.date()}: {self.amount}"


class DisposableIncomeSpending(models.Model):
    """
    Represents a spending entry deducted from the user's disposable budget.
    """
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="disposable_income_spending"
    )
    title = models.CharField(
        max_length=50,
        blank=False,
        help_text="Short description of the expenditure."
    )
    amount = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(1_000_000)],
        help_text="Amount spent in pence."
    )
    date = models.DateTimeField(
        blank=False,
        help_text="Date and time of the spending entry."
    )

    class Meta:
        ordering = ['-date']
        verbose_name = "Disposable Income Spending"

    def __str__(self):
        return f"{self.owner.username} spent {self.amount} on {self.title} ({self.date.date()})"
