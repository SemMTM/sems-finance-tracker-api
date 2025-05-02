from datetime import timedelta
from calendar import monthrange
from .models import Expenditure, Income
import uuid
from dateutil.relativedelta import relativedelta


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


def process_monthly_repeats(user, model, current_month_start):
    """
    Generic monthly repeat processor for Income or Expenditure model.
    Handles both MONTHLY and WEEKLY repeated entries.
    """
    last_month_start = current_month_start - relativedelta(months=1)
    last_month_end = last_month_start.replace(
        day=monthrange(last_month_start.year, last_month_start.month)[1]
    )

    print(Income.objects.filter(owner=user).values("title", "date", "repeated"))

    repeated_items = model.objects.filter(
        owner=user,
        date__gte=last_month_start,
        date__lte=last_month_end,
        repeated__in=["MONTHLY", "WEEKLY"]
    )

    print(f"Processing monthly repeats for {user.username}, month: {current_month_start}")
    print(f"Found {repeated_items.count()} repeated entries")

    for item in repeated_items:
        if item.repeated == "MONTHLY":
            new_date = item.date + relativedelta(months=1)
            last_day = monthrange(new_date.year, new_date.month)[1]
            if new_date.day > last_day:
                new_date = new_date.replace(day=last_day)

            if not model.objects.filter(
                owner=item.owner,
                title=item.title,
                amount=item.amount,
                date=new_date,
                repeated="MONTHLY",
                **({'type': item.type} if model.__name__ == 'Expenditure' else {})
            ).exists():
                model.objects.create(
                    owner=item.owner,
                    title=item.title,
                    amount=item.amount,
                    date=new_date,
                    repeated="MONTHLY",
                    **({'type': item.type} if model.__name__ == 'Expenditure' else {})
                )

                print(f"Creating new income for {new_date}")

        elif item.repeated == "WEEKLY" and item.repeat_group_id:
            group_items = model.objects.filter(
                owner=user,
                repeat_group_id=item.repeat_group_id,
                date__gte=last_month_start,
                date__lte=last_month_end
            )

            for entry in group_items:
                new_date = entry.date + relativedelta(months=1)
                last_day = monthrange(new_date.year, new_date.month)[1]
                if new_date.day > last_day:
                    new_date = new_date.replace(day=last_day)

                if not model.objects.filter(
                    owner=entry.owner,
                    title=entry.title,
                    amount=entry.amount,
                    date=new_date,
                    repeated="WEEKLY",
                    repeat_group_id=entry.repeat_group_id,
                    **({'type': entry.type} if model.__name__ == 'Expenditure' else {})
                ).exists():
                    model.objects.create(
                        owner=entry.owner,
                        title=entry.title,
                        amount=entry.amount,
                        date=new_date,
                        repeated="WEEKLY",
                        repeat_group_id=entry.repeat_group_id,
                        **({'type': entry.type} if model.__name__ == 'Expenditure' else {})
                    )