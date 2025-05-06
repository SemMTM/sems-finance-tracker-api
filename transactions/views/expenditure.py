from rest_framework import viewsets, permissions
from rest_framework.response import Response
import uuid
from rest_framework.exceptions import PermissionDenied
from ..models.expenditure import Expenditure
from ..serializers.expenditure import ExpenditureSerializer
from core.utils.date_helpers import get_user_and_month_range
from ..utils import (generate_weekly_repeats_for_6_months,
                     generate_monthly_repeats_for_6_months)


class ExpenditureViewSet(viewsets.ModelViewSet):
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
        instance = serializer.save(owner=self.request.user)

        # Check if instance is repeated weekly or monthly
        if instance.repeated == 'WEEKLY':
            generate_weekly_repeats_for_6_months(instance, Expenditure)
        elif instance.repeated == 'MONTHLY':
            generate_monthly_repeats_for_6_months(instance, Expenditure)

    def get_object(self):
        """
        Ensures the user only accesses their own object.
        """
        obj = Expenditure.objects.get(pk=self.kwargs['pk'])

        if obj.owner != self.request.user:
            raise PermissionDenied(
                "You do not have permission to access this expenditure.")
        return obj

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # If repeated, delete all future entries in the same repeat group
        if instance.repeated in ['WEEKLY', 'MONTHLY'] and instance.repeat_group_id:
            future_entries = Expenditure.objects.filter(
                owner=request.user,
                repeat_group_id=instance.repeat_group_id,
                date__gte=instance.date
            )
            future_entries.delete()
        else:
            instance.delete()

        return Response(status=204)

    def perform_update(self, serializer):
        instance = serializer.save()

        # Only apply group updates if the entry is repeated
        if instance.repeated in ['WEEKLY', 'MONTHLY'] and instance.repeat_group_id:
            new_group_id = uuid.uuid4()

            future_entries = Expenditure.objects.filter(
                owner=self.request.user,
                repeat_group_id=serializer.instance.repeat_group_id,
                date__gt=instance.date)

            # Update the edited instance with the new group ID
            instance.repeat_group_id = new_group_id
            instance.save(update_fields=['repeat_group_id'])

            # Update all future entries (same group, same user, after the edited date)
            future_entries.update(
                title=instance.title,
                amount=instance.amount,
                repeated=instance.repeated,
                repeat_group_id=new_group_id,
                type=instance.type
            )
