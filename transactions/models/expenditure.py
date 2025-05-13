from django.db import models
from django.contrib.auth.models import User
import uuid  # noqa
from .shared import REPEATED_CHOICES, TYPE


class Expenditure(models.Model):
    """
    Represents an expenditure entry

    Fields:
        - owner: the user who owns this expenditure
        - title: short description of the expenditure
        - amount: value in pence (always stored as integer)
        - repeated: frequency of recurrence (e.g., monthly, never)
        - type: category label (e.g., BILL, SAVING)
        - date: datetime the expenditure applies to
        - repeat_group_id: UUID used to group repeated entries
    """
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="expenditures"
    )
    title = models.CharField(
        max_length=100,
        blank=False,
        help_text="Name or label for this expenditure."
    )
    amount = models.PositiveIntegerField(
        help_text="Amount in pence (e.g., £12.99 = 1299)."
    )
    repeated = models.CharField(
        choices=REPEATED_CHOICES,
        default='NEVER',
        blank=False,
        help_text="Repetition frequency (e.g., NEVER, MONTHLY)."
    )
    type = models.CharField(
        choices=TYPE,
        blank=False,
        default='BILL',
        help_text="Type/category of expenditure."
    )
    date = models.DateTimeField(
        help_text="Date and time the expenditure applies to."
    )
    repeat_group_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Used to group related repeated entries."
    )

    class Meta:
        ordering = ['-date']
        verbose_name = "Expenditure"
        verbose_name_plural = "Expenditures"

    def __str__(self) -> str:
        return f"{self.owner} Expenditure: {self.title} - {self.amount}"
