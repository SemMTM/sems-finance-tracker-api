from django.utils.timezone import now
from datetime import timedelta


def get_user_and_month_range(request):
    """
    Returns a tuple: (user, start_of_month, end_of_month)
    Based on the current user's timezone-aware request time.
    """
    user = request.user
    current_date = now()

    start_of_month = current_date.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0)

    if start_of_month.month == 12:
        end_of_month = start_of_month.replace(
            year=start_of_month.year + 1, month=1)
    else:
        end_of_month = start_of_month.replace(
            month=start_of_month.month + 1)

    return user, start_of_month, end_of_month


def get_weeks_in_month_clipped(request):
    """
    Returns a list of (start, end) datetime tuples for each week in the current month.
    Weeks are clipped to not exceed the month's boundaries.
    """
    user, start_of_month, end_of_month = get_user_and_month_range(request)

    weeks = []
    current = start_of_month

    while current < end_of_month:
        week_start = current
        week_end = week_start + timedelta(days=6 - week_start.weekday()) + timedelta(days=1)  # end is exclusive
        week_end = min(week_end, end_of_month)
        weeks.append((week_start, week_end))
        current = week_end

    return user, weeks, start_of_month, end_of_month
