from django.utils.timezone import now
from transactions.utils import generate_6th_month_repeats
from transactions.models import Income, Expenditure
from core.models import UserProfile


def check_and_run_monthly_repeat(user):
    today = now().date()
    current_month = today.replace(day=1)

    profile, _ = UserProfile.objects.get_or_create(user=user)

    if profile.last_repeat_check == current_month:
        return

    generate_6th_month_repeats(Income, user, current_month)
    generate_6th_month_repeats(Expenditure, user, current_month)

    profile.last_repeat_check = current_month
    profile.save(update_fields=["last_repeat_check"])
