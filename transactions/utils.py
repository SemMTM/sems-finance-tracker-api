from datetime import timedelta
from calendar import monthrange
from .models import Expenditure, Income
import uuid


def generate_weekly_repeats(instance):
    """
    Generate repeated weekly Expenditure entries within the same month as `instance`.
    """
    original_date = instance.date
    year = original_date.year
    month = original_date.month

    if not instance.repeat_group_id:
        instance.repeat_group_id = uuid.uuid4()
        instance.save(update_fields=["repeat_group_id"])

    # Get the last day of the month
    last_day = monthrange(year, month)[1]

    # Keep track of new dates 7 days apart
    new_dates = []
    current_date = original_date + timedelta(days=7)

    # Keep adding +7 days as long as it's within the same month
    while current_date.month == month and current_date.day <= last_day:
        new_dates.append(current_date)
        current_date += timedelta(days=7)

    # Prepare bulk create objects
    repeat_entries = [
        Expenditure(
            owner=instance.owner,
            title=instance.title,
            amount=instance.amount,
            date=date,
            type=instance.type,
            repeated=instance.repeated,
            repeat_group_id=instance.repeat_group_id
        )
        for date in new_dates
    ]

    Expenditure.objects.bulk_create(repeat_entries)


def generate_weekly_income_repeats(instance):
    """
    Generate repeated weekly Income entries within the same month.
    """
    original_date = instance.date
    year = original_date.year
    month = original_date.month
    last_day = monthrange(year, month)[1]

    # Assign a group ID if missing
    if not instance.repeat_group_id:
        instance.repeat_group_id = uuid.uuid4()
        instance.save(update_fields=["repeat_group_id"])

    current_date = original_date + timedelta(days=7)
    new_dates = []

    while current_date.month == month and current_date.day <= last_day:
        new_dates.append(current_date)
        current_date += timedelta(days=7)

    repeat_entries = [
        Income(
            owner=instance.owner,
            title=instance.title,
            amount=instance.amount,
            date=date,
            repeated=instance.repeated,
            repeat_group_id=instance.repeat_group_id,
        )
        for date in new_dates
    ]

    Income.objects.bulk_create(repeat_entries)
