from django.utils.timezone import now
from transactions.utils import generate_6th_month_repeats
from transactions.models import Income, Expenditure
from core.models import UserProfile
from django.contrib.auth.models import User


def check_and_run_monthly_repeat(user: User) -> None:
    """
    Ensures that monthly repeated entries for Income and Expenditure
    are generated only once per month for a given user.

    - Uses UserProfile.last_repeat_check to track last run month.
    - If repeats for current month were already generated, the function
      exits early.
    - Otherwise, it triggers repeat generation and updates the profile.

    Args:
        user (User): The Django user object whose data should be processed.
    """
    today = now().date()
    current_month = today.replace(day=1)

    # Ensure user profile exists
    profile, _ = UserProfile.objects.get_or_create(user=user)

    # Skip if repeats have already been generated this month
    if profile.last_repeat_check == current_month:
        return

    # Generate repeated entries
    generate_6th_month_repeats(Income, user, current_month)
    generate_6th_month_repeats(Expenditure, user, current_month)

    # Update last repeat check timestamp
    profile.last_repeat_check = current_month
    profile.save(update_fields=["last_repeat_check"])
