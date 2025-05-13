from django.db import models
from django.contrib.auth.models import User
from .shared import REPEATED_CHOICES
import uuid  # noqa


class Income(models.Model):
    """
    Represents a recurring or one-off income source for the user.

    Fields:
        - owner: linked User
        - title: description of the income (e.g. Salary, Freelance)
        - amount: stored in pence (int)
        - date: date the income applies to
        - repeated: repetition frequency (DAILY, WEEKLY, MONTHLY, NEVER)
        - repeat_group_id: groups repeated entries for bulk deletion/update
    """
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="incomes"
    )
    title = models.CharField(
        max_length=100,
        blank=False,
        help_text="Short label for this income source."
    )
    amount = models.PositiveIntegerField(
        blank=False,
        help_text="Income amount in pence (e.g., £1200 = 120000)."
    )
    date = models.DateTimeField(
        blank=False,
        help_text="Date the income applies to."
    )
    repeated = models.CharField(
        choices=REPEATED_CHOICES,
        default='NEVER',
        blank=False,
        help_text="Repetition frequency of the income entry."
    )
    repeat_group_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="ID for grouping repeated "
        "incomes (used for bulk updates/deletes)."
    )

    class Meta:
        ordering = ['-date']
        verbose_name = "Income"
        verbose_name_plural = "Incomes"

    def __str__(self) -> str:
        return f"{self.owner.username} Income: {self.title} - {self.amount}"
