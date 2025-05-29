from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
import uuid
from ..models.expenditure import Expenditure
from ..serializers.expenditure import ExpenditureSerializer
from core.utils.date_helpers import get_user_and_month_range
from ..utils import (
    generate_weekly_repeats_for_6_months,
    generate_monthly_repeats_for_6_months,
    repeat_on_date_change
)


class ExpenditureViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD for a user's monthly expenditure entries.

    Includes:
    - Automatic generation of repeated entries (weekly/monthly)
    - Grouped deletion of future repeated entries
    - Group-aware update propagation
    """
    serializer_class = ExpenditureSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return this user's expenditures for the current month only.
        """
        user, start, end = get_user_and_month_range(self.request)
        return Expenditure.objects.filter(
            owner=user,
            date__gte=start,
            date__lt=end
        ).order_by('date')

    def perform_create(self, serializer):
        """
        Saves the new expenditure and triggers repeat generation if applicable.
        """
        instance = serializer.save(owner=self.request.user)

        # Check if instance is repeated weekly or monthly
        if instance.repeated == 'WEEKLY':
            generate_weekly_repeats_for_6_months(instance, Expenditure)
        elif instance.repeated == 'MONTHLY':
            generate_monthly_repeats_for_6_months(instance, Expenditure)

    def get_object(self):
        """
        Ensures the current user is the owner of the expenditure.
        """
        obj = obj = Expenditure.objects.get(pk=self.kwargs['pk'])
        if obj.owner != self.request.user:
            raise PermissionDenied(
                "You do not have permission to access this expenditure.")
        return obj

    def destroy(self, request, *args, **kwargs):
        """
        Deletes this expenditure and all future instances in
        the same repeat group,
        if applicable.
        """
        instance = self.get_object()

        # If repeated, delete all future entries in the same repeat group
        if (
            instance.repeated in ['WEEKLY', 'MONTHLY']
            and instance.repeat_group_id
        ):
            Expenditure.objects.filter(
                owner=request.user,
                repeat_group_id=instance.repeat_group_id,
                date__gte=instance.date
            ).delete()
        else:
            instance.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT)

    def perform_update(self, serializer):
        """
        Updates the expenditure and propagates changes to future
        repeated entries.
        """
        original = self.get_object()
        instance = serializer.save()

        # Check if this is a repeated entry with a date change
        if (
            instance.repeated in ['WEEKLY', 'MONTHLY']
            and instance.repeat_group_id
            and instance.date != original.date
        ):
            # Handle regeneration logic and exit early
            repeat_on_date_change(instance, model_class=Expenditure)
            return

        old_group_id = instance.repeat_group_id
        new_group_id = uuid.uuid4()

        # Update the edited instance with the new group ID
        instance.repeat_group_id = new_group_id
        instance.save(update_fields=['repeat_group_id'])

        # Update future entries in the group
        Expenditure.objects.filter(
            owner=self.request.user,
            repeat_group_id=old_group_id,
            date__gt=instance.date
        ).update(
            title=instance.title,
            amount=instance.amount,
            repeated=instance.repeated,
            repeat_group_id=new_group_id,
            type=instance.type
        )
