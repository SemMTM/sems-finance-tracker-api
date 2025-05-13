from django.utils.timezone import now, make_aware
from django.http import HttpRequest
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta


def get_user_and_month_range(request: HttpRequest):
    """
    Extracts the user and a timezone-aware datetime range for
    the specified month.

    Args:
        request (HttpRequest): Incoming request that may contain
        ?month=YYYY-MM.

    Returns:
        tuple: (user, start_of_month, end_of_month)
            - start_of_month is the first day of the month at 00:00
            - end_of_month is exclusive (start of next month)
    """
    user = request.user
    month_param = request.GET.get("month")

    def get_default_start():
        return now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if month_param:
        try:
            # Parse naive datetime from YYYY-MM string
            naive_start = datetime.strptime(month_param, "%Y-%m")
            # Convert to timezone-aware and standardize time to 00:00
            start_of_month = make_aware(naive_start.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0))
        except ValueError:
            # Fallback if parsing fails
            start_of_month = get_default_start()
    else:
        # Default to current month
        start_of_month = get_default_start()

    # Add 1 month to get exclusive end boundary
    end_of_month = start_of_month + relativedelta(months=1)
    return user, start_of_month, end_of_month


def get_weeks_in_month_clipped(request: HttpRequest):
    """
    Generates weekly ranges (start, end) clipped to the bounds
    of the current month.

    Args:
        request (HttpRequest): The current request to extract month/user from.

    Returns:
        tuple: (user, weeks, start_of_month, end_of_month)
            - weeks: list of (start_datetime, end_datetime) tuples for
              each week.
            - Week ends are capped at the end of the month.
    """
    user, start_of_month, end_of_month = get_user_and_month_range(request)

    weeks = []
    current = start_of_month

    while current < end_of_month:
        week_start = current

        # Week ends Sunday, but clipped to not go past end_of_month
        days_until_sunday = 6 - week_start.weekday()
        week_end = min(week_start + timedelta(
            days=days_until_sunday + 1), end_of_month)

        # Only include the week if it falls at least partially inside the month
        weeks.append((week_start, week_end))
        current = week_end

    return user, weeks, start_of_month, end_of_month
