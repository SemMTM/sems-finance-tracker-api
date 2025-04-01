from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from core.utils.date_helpers import get_user_and_month_range
from ..models.disposable import DisposableIncomeSpending
from ..serializers.disposable import DisposableIncomeSpendingSerializer


class DisposableIncomeSpendingViewSet(viewsets.ModelViewSet):
    """
    Handles disposable income spending entries for the current user and month.
    """
    serializer_class = DisposableIncomeSpendingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user, start, end = get_user_and_month_range(self.request)

        return DisposableIncomeSpending.objects.filter(
            owner=user,
            date__gte=start,
            date__lt=end
        ).order_by('date')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_object(self):
        obj = super().get_object()
        if obj.owner != self.request.user:
            raise PermissionDenied(
                "You do not have permission to access this entry.")
        return obj
