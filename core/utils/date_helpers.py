from django.utils.timezone import now


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
