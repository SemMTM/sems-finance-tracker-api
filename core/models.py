from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    Stores user-specific metadata for financial automation logic,
    such as when recurring income and expenditure entries were last generated.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    last_repeat_check = models.DateField(
        null=True,
        blank=True,
        help_text="The first day of the last month when repeats were generated."
    )

    def __str__(self) -> str:
        return f"{self.user.username} profile"
