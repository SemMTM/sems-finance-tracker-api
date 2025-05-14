from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from core.utils.date_helpers import get_user_and_month_range
from ..models.disposable import DisposableIncomeSpending
from ..serializers.disposable import DisposableIncomeSpendingSerializer


class DisposableIncomeSpendingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing disposable income spending entries.

    - Filters spending to only the current user and month
    - Automatically assigns ownership on creation
    - Enforces ownership on retrieve/update/delete
    """
    serializer_class = DisposableIncomeSpendingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Restricts queryset to the current authenticated user's
        entries for the selected or current month.
        """
        user, start, end = get_user_and_month_range(self.request)
        return DisposableIncomeSpending.objects.filter(
            owner=user,
            date__gte=start,
            date__lt=end
        ).order_by('date')

    def perform_create(self, serializer):
        """
        Sets the owner of the new spending entry to the current user.
        """
        serializer.save(owner=self.request.user)

    def get_object(self):
        """
        Ensures that only the owner can access the spending entry.
        """
        obj = obj = DisposableIncomeSpending.objects.get(pk=self.kwargs['pk'])
        if obj.owner != self.request.user:
            raise PermissionDenied(
                "You do not have permission to access this entry.")
        return obj
