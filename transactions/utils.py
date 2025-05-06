from datetime import timedelta
from dateutil.relativedelta import relativedelta
from calendar import monthrange
import uuid


def generate_weekly_repeats_for_6_months(instance, model_class):
    """
    Repeats an entry weekly for 6 months from its original date.
    `model_class` is either Expenditure or Income.
    """
    if not instance.repeat_group_id:
        instance.repeat_group_id = uuid.uuid4()
        instance.save(update_fields=["repeat_group_id"])

    repeats = []
    base_date = instance.date
    final_date = base_date + relativedelta(months=6)

    current_date = base_date + timedelta(days=7)
    while current_date <= final_date:
        repeats.append(current_date)
        current_date += timedelta(days=7)

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

    for i in range(1, 6):  # Already created for month 0
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
