from django.utils.timezone import make_aware
from dateutil.relativedelta import relativedelta
from django.utils.timezone import now
from datetime import timedelta, time, datetime
from calendar import monthrange
from transactions.models import (
    Income,
    Expenditure,
    DisposableIncomeSpending,
    DisposableIncomeBudget,
)
import uuid


def generate_weekly_repeats_for_6_months(instance, model_class):
    """
    Repeats an entry weekly for 6 months from its original date.
    No entries are created beyond the end of the month that is 5 months ahead.
    """
    if not instance.repeat_group_id:
        instance.repeat_group_id = uuid.uuid4()
        instance.save(update_fields=["repeat_group_id"])

    base_date = instance.date
    # Define the last valid visible date = start of base month + 5 months
    final_month = base_date.replace(day=1) + relativedelta(months=5)
    final_day = monthrange(
        final_month.year, final_month.month)[1]
    final_visible_date = final_month.replace(day=final_day)

    # Generate repeated weekly dates
    current_date = base_date + timedelta(days=7)
    repeats = []

    while current_date <= final_visible_date:
        repeats.append(current_date)
        current_date += timedelta(days=7)

    _bulk_create_repeats(instance, model_class, repeats)


def generate_monthly_repeats_for_6_months(instance, model_class):
    """
    Repeats an entry monthly for 6 months from its original date.
    Adjusts days to avoid invalid dates (e.g., Feb 30).
    """
    if not instance.repeat_group_id:
        instance.repeat_group_id = uuid.uuid4()
        instance.save(update_fields=["repeat_group_id"])

    repeats = []
    base_date = instance.date

    for i in range(1, 6):
        new_date = base_date + relativedelta(months=i)
        last_day = monthrange(new_date.year, new_date.month)[1]
        new_date = new_date.replace(day=min(base_date.day, last_day))
        repeats.append(new_date)

    _bulk_create_repeats(instance, model_class, repeats)


def generate_6th_month_repeats(model_class, user, current_month):
    """
    Generate repeated entries for the 6th visible month (current + 5)
    by checking existing repeated entries in the 5th month (current + 4).
    Avoids duplicate generation. Handles both weekly and monthly types.
    """
    # Define 5th and 6th months
    fifth_month = current_month + relativedelta(months=4)
    sixth_month = current_month + relativedelta(months=5)

    # Get timezone-aware datetime bounds for both
    fifth_start = make_aware(datetime.combine(
        fifth_month.replace(day=1), time.min))
    fifth_end = make_aware(datetime.combine(
        fifth_month.replace(day=monthrange(
            fifth_month.year, fifth_month.month)[1]),
        time.min
    ))

    sixth_end = make_aware(datetime.combine(
        sixth_month.replace(day=monthrange(
            sixth_month.year, sixth_month.month)[1]),
        time.min
    ))

    new_entries = []

    # ---- 1. Monthly repeats ----
    monthly_entries = model_class.objects.filter(
        owner=user,
        repeated='MONTHLY',
        date__gte=fifth_start,
        date__lte=fifth_end
    )

    for entry in monthly_entries:
        new_date = entry.date + relativedelta(months=1)
        max_day = monthrange(new_date.year, new_date.month)[1]
        new_date = new_date.replace(day=min(entry.date.day, max_day))

        if not model_class.objects.filter(
            owner=user,
            repeat_group_id=entry.repeat_group_id,
            date=new_date
        ).exists():
            new_entries.append(_clone_entry(entry, new_date))

    # ---- 2. Weekly repeats ----
    group_ids = set(model_class.objects.filter(
        owner=user,
        repeated='WEEKLY',
        date__gte=fifth_start,
        date__lte=fifth_end,
        repeat_group_id__isnull=False
    ).values_list('repeat_group_id', flat=True))

    for group_id in group_ids:
        last_entry = model_class.objects.filter(
            owner=user,
            repeat_group_id=group_id,
            date__gte=fifth_start,
            date__lte=fifth_end
        ).order_by('-date').first()

        if not last_entry:
            continue

        next_date = last_entry.date + timedelta(days=7)
        while next_date <= sixth_end:
            if not model_class.objects.filter(
                owner=user,
                repeat_group_id=group_id,
                date=next_date
            ).exists():
                new_entries.append(_clone_entry(last_entry, next_date))
            next_date += timedelta(days=7)

    # ---- 3. Create all entries at once ----
    if new_entries:
        model_class.objects.bulk_create(new_entries)


def _clone_entry(entry, date):
    """
    Creates a copy of a financial entry with a new date.
    """
    data = {
        'owner': entry.owner,
        'title': entry.title,
        'amount': entry.amount,
        'date': date,
        'repeated': entry.repeated,
        'repeat_group_id': entry.repeat_group_id
    }
    if hasattr(entry, 'type'):
        data['type'] = entry.type
    return entry.__class__(**data)


def _bulk_create_repeats(instance, model_class, date_list):
    """
    Helper to bulk-create repeated entries based on a list of dates.
    """
    entries = [
        model_class(
            owner=instance.owner,
            title=instance.title,
            amount=instance.amount,
            date=date,
            repeated=instance.repeated,
            repeat_group_id=instance.repeat_group_id,
            **({'type': instance.type} if hasattr(instance, 'type') else {})
        )
        for date in date_list
    ]
    model_class.objects.bulk_create(entries)


def clean_old_transactions(user):
    """
    Deletes all of a user's financial records that are older than
    the start of the visible window (current month - 5 months).
    """
    # 1. Get current month as datetime (first day of month)
    current_month_start = now().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0)

    # 2. Calculate the cutoff date (start of current month - 6 months)
    cutoff_date = current_month_start - relativedelta(months=6)

    # 3. Models to clean
    transaction_models = [
        Income,
        Expenditure,
        DisposableIncomeSpending,
        DisposableIncomeBudget,
    ]

    # 4. Loop through and delete anything outside the visible window
    for model in transaction_models:
        model.objects.filter(owner=user, date__lt=cutoff_date).delete()
