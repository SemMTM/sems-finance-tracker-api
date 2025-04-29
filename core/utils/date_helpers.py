from django.utils.timezone import now, make_aware
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta


def get_user_and_month_range(request):
    """
    Returns a tuple: (user, start_of_month, end_of_month)
    - Uses ?month=YYYY-MM if provided in the query string
    - Defaults to current month if not specified
    - Ensures timezone-aware datetime output
    """
    user = request.user
    month_param = request.query_params.get("month")

    if month_param:
        try:
            # Parse naive datetime from YYYY-MM string
            naive_start = datetime.strptime(month_param, "%Y-%m")
            # Convert to timezone-aware and standardize time to 00:00
            start_of_month = make_aware(naive_start.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0))
        except ValueError:
            # Fallback if parsing fails
            start_of_month = now().replace(
                day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        # Default to current month
        start_of_month = now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0)

    # Add 1 month to get exclusive end boundary
    end_of_month = start_of_month + relativedelta(months=1)

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
