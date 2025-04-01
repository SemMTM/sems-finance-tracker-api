from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from ..models.income import Income
from ..serializers.income import IncomeSerializer
from core.utils.date_helpers import get_user_and_month_range


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
        serializer.save(owner=self.request.user)

    def get_object(self):
        """
        Restrict object-level access to the owner only.
        """
        obj = super().get_object()
        if obj.owner != self.request.user:
            raise PermissionDenied("You do not have permission to access this income entry.")
        return obj
