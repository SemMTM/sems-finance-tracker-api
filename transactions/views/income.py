from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from django.utils.timezone import now
from ..models.income import Income
from ..serializers.income import IncomeSerializer


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
        user = self.request.user
        current_date = now()
        start_of_month = current_date.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0)

        if start_of_month.month == 12:
            end_of_month = start_of_month.replace(
                year=start_of_month.year + 1, month=1)
        else:
            end_of_month = start_of_month.replace(
                month=start_of_month.month + 1)

        return Income.objects.filter(
            owner=user,
            date__gte=start_of_month,
            date__lt=end_of_month
        ).order_by('date')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_object(self):
        """
        Restrict object-level access to the owner only.
        """
        obj = super().get_object()
        if obj.owner != self.request.user:
            raise PermissionDenied("You do not have permission to access this income entry.")
        return obj
