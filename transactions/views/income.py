from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from ..models.income import Income
from ..serializers.income import IncomeSerializer
from core.utils.date_helpers import get_user_and_month_range
from ..utils import (
    generate_weekly_repeats_for_6_months,
    generate_monthly_repeats_for_6_months,
    repeat_on_date_change
)
import uuid


class IncomeViewSet(viewsets.ModelViewSet):
    """
    Handles listing, creating, updating, and deleting income entries
    for the current user within the selected or current month.
    """
    serializer_class = IncomeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return this user's income entries for the selected month.
        """
        user, start, end = get_user_and_month_range(self.request)
        return Income.objects.filter(
            owner=user,
            date__gte=start,
            date__lt=end
        ).order_by('date')

    def perform_create(self, serializer):
        """
        Saves the income entry and triggers repeat generation if required.
        """
        instance = serializer.save(owner=self.request.user)

        if instance.repeated == 'WEEKLY':
            generate_weekly_repeats_for_6_months(instance, Income)
        elif instance.repeated == 'MONTHLY':
            generate_monthly_repeats_for_6_months(instance, Income)

    def destroy(self, request, *args, **kwargs):
        """
        Deletes a single income or all future repeated entries in the
        same group.
        """
        instance = self.get_object()

        # If repeated, delete all future entries in the same repeat group
        if (
            instance.repeated in ['WEEKLY', 'MONTHLY']
            and instance.repeat_group_id
        ):
            Income.objects.filter(
                owner=request.user,
                repeat_group_id=instance.repeat_group_id,
                date__gte=instance.date
            ).delete()
        else:
            instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_object(self):
        """
        Restrict object-level access to the owner only.
        """
        obj = Income.objects.get(pk=self.kwargs['pk'])

        if obj.owner != self.request.user:
            raise PermissionDenied(
                "You do not have permission to access this income entry.")
        return obj

    def perform_update(self, serializer):
        """
        Handles update logic for Income entries, including repeated entries.

        If the updated entry is part of a repeated series
        and its date has changed:
        - Delete the current and all future entries in the same repeat group.
        - Create a new entry with updated data and regenerate
        the repeat chain with a new group ID.

        If the date has not changed but the entry is repeated:
        - Assign a new group ID to the edited instance.
        - Update all future entries in the original group to reflect
        the changes
        (e.g. title, amount, repeated) and apply the new group ID.
        """
        # Fetch the original (pre-update) version to compare the date
        original = self.get_object()

        instance = serializer.save()

        # Check if this is a repeated entry with a date change
        if (
            instance.repeated in ['WEEKLY', 'MONTHLY']
            and instance.repeat_group_id
            and instance.date != original.date
        ):

            # Handle regeneration logic and exit early
            repeat_on_date_change(instance, model_class=Income)
            return

        old_group_id = instance.repeat_group_id
        new_group_id = uuid.uuid4()

        # Update the edited instance with the new group ID
        instance.repeat_group_id = new_group_id
        instance.save(update_fields=['repeat_group_id'])

        future_entries = Income.objects.filter(
            owner=self.request.user,
            repeat_group_id=old_group_id,
            date__gt=instance.date)

        # Update all future entries (same group, same user,
        # after the edited date)
        future_entries.update(
            title=instance.title,
            amount=instance.amount,
            repeated=instance.repeated,
            repeat_group_id=new_group_id
        )
