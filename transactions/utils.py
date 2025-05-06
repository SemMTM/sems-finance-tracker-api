from datetime import timedelta
from dateutil.relativedelta import relativedelta
from calendar import monthrange
import uuid


def generate_weekly_repeats_for_6_months(instance, model_class):
    """
    Repeats an entry weekly for 6 months from its original date,
    but does not create entries beyond the current month + 5 months window.
    `model_class` is either Expenditure or Income.
    """
    if not instance.repeat_group_id:
        instance.repeat_group_id = uuid.uuid4()
        instance.save(update_fields=["repeat_group_id"])

    base_date = instance.date

    # Define the last valid visible date = start of base month + 5 months
    final_visible_date = base_date.replace(day=1) + relativedelta(months=5)
    final_day = monthrange(final_visible_date.year, final_visible_date.month)[1]
    final_visible_date = final_visible_date.replace(day=final_day)

    # Generate repeated weekly dates
    repeats = []
    current_date = base_date + timedelta(days=7)
    while current_date <= final_visible_date:
        repeats.append(current_date)
        current_date += timedelta(days=7)

    # Bulk create entries that fall within the limit
    model_class.objects.bulk_create([
        model_class(
            owner=instance.owner,
            title=instance.title,
            amount=instance.amount,
            date=date,
            repeated=instance.repeated,
            repeat_group_id=instance.repeat_group_id,
            **({'type': instance.type} if hasattr(instance, 'type') else {})
        )
        for date in repeats
    ])


def generate_monthly_repeats_for_6_months(instance, model_class):
    """
    Repeats an entry monthly for 6 months from its original date.
    `model_class` is either Expenditure or Income.
    """
    if not instance.repeat_group_id:
        instance.repeat_group_id = uuid.uuid4()
        instance.save(update_fields=["repeat_group_id"])

    repeats = []
    base_date = instance.date

    for i in range(1, 6):
        new_date = base_date + relativedelta(months=i)
        last_day = monthrange(new_date.year, new_date.month)[1]
        adjusted_day = min(base_date.day, last_day)
        new_date = new_date.replace(day=adjusted_day)
        repeats.append(new_date)

    model_class.objects.bulk_create([
        model_class(
            owner=instance.owner,
            title=instance.title,
            amount=instance.amount,
            date=date,
            repeated=instance.repeated,
            repeat_group_id=instance.repeat_group_id,
            **({'type': instance.type} if hasattr(instance, 'type') else {})
        ) for date in repeats
    ])


def generate_6th_month_repeats(model_class, user, current_month):
    """
    For the 6th visible month (current + 5), generate repeat entries
    by checking the 5th month (current + 4) for anything with a repeated flag.
    Adds 1 month to each and ensures no duplicates.
    """
    # Calculate 5th and 6th month boundaries
    fifth_month = current_month + relativedelta(months=4)
    sixth_month = current_month + relativedelta(months=5)

    fifth_start = fifth_month.replace(day=1)
    fifth_end = fifth_start.replace(
        day=monthrange(fifth_start.year, fifth_start.month)[1])

    sixth_start = sixth_month.replace(day=1)
    sixth_end = sixth_start.replace(
        day=monthrange(sixth_start.year, sixth_start.month)[1])

    # Get all repeatable entries from 5th month
    repeated_entries = model_class.objects.filter(
        owner=user,
        repeated__in=['WEEKLY', 'MONTHLY'],
        date__gte=fifth_start,
        date__lte=fifth_end
    )

    new_entries = []

    for entry in repeated_entries:
        # Add 1 month
        proposed_date = entry.date + relativedelta(months=1)

        # Adjust day if it overflows the target month
        last_day = monthrange(proposed_date.year, proposed_date.month)[1]
        if proposed_date.day > last_day:
            proposed_date = proposed_date.replace(day=last_day)

        # Only create if not already present
        exists = model_class.objects.filter(
            owner=user,
            repeat_group_id=entry.repeat_group_id,
            date=proposed_date
        ).exists()

        if not exists:
            kwargs = {
                'owner': user,
                'title': entry.title,
                'amount': entry.amount,
                'date': proposed_date,
                'repeated': entry.repeated,
                'repeat_group_id': entry.repeat_group_id,
            }
            if hasattr(entry, 'type'):
                kwargs['type'] = entry.type

            new_entries.append(model_class(**kwargs))

    if new_entries:
        model_class.objects.bulk_create(new_entries)
