from datetime import datetime
from dateutil.relativedelta import relativedelta
from transactions.models import Income, Expenditure
from transactions.utils import generate_6th_month_repeats


last_processed = {}


def run_month_rollover_logic(user, current_month):
    """
    Trigger repeat entry generation for the 6th visible month.
    Only runs once per user per month.
    """
    # Normalize month to first of the month
    normalized_month = current_month.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0)

    # Check if already processed for this user and month
    cache_key = f"{user.id}_{normalized_month.isoformat()}"
    if last_processed.get(user.id) == normalized_month:
        return  # Already handled for this user/month

    # Run repeat logic for Income and Expenditure
    generate_6th_month_repeats(Income, user, normalized_month)
    generate_6th_month_repeats(Expenditure, user, normalized_month)

    # Store last run marker
    last_processed[user.id] = normalized_month
