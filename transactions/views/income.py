from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from ..models.income import Income
from ..serializers.income import IncomeSerializer
from core.utils.date_helpers import get_user_and_month_range
from ..utils import generate_weekly_income_repeats


class IncomeViewSet(viewsets.ModelViewSet):
    """
    Handles listing, creating, updating, and
    deleting income entries for the current user and month.
    """
    serializer_class = IncomeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return this user's income entries for the current month.
        """
        user, start, end = get_user_and_month_range(self.request)

        return Income.objects.filter(
            owner=user,
            date__gte=start,
            date__lt=end
        ).order_by('date')

    def perform_create(self, serializer):
        instance = serializer.save(owner=self.request.user)

        if instance.repeated == 'WEEKLY':
            generate_weekly_income_repeats(instance)

    from rest_framework.response import Response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.repeated == 'WEEKLY' and instance.repeat_group_id:
            Income.objects.filter(
                owner=request.user,
                repeat_group_id=instance.repeat_group_id,
                date__gte=instance.date
            ).delete()
            return Response(status=204)

        return super().destroy(request, *args, **kwargs)

    def get_object(self):
        """
        Restrict object-level access to the owner only.
        """
        obj = super().get_object()
        if obj.owner != self.request.user:
            raise PermissionDenied("You do not have permission to access this income entry.")
        return obj

    def perform_update(self, serializer):
        instance = serializer.save()

        if instance.repeated == 'WEEKLY' and instance.repeat_group_id:
            Income.objects.filter(
                owner=self.request.user,
                repeat_group_id=instance.repeat_group_id,
                date__gte=instance.date
            ).exclude(id=instance.id).update(
                title=instance.title,
                amount=instance.amount,
            )