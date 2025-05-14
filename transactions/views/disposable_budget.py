from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from django.utils.timezone import now, make_aware
from datetime import datetime
from ..models.disposable import DisposableIncomeBudget
from ..serializers.disposable import DisposableIncomeBudgetSerializer
from core.utils.date_helpers import get_user_and_month_range


class DisposableIncomeBudgetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing a user's monthly disposable income budget.

    Behavior:
    - Automatically creates a 0-value budget for the current month if not present
    - Restricts access to only the user's current-month budget
    - Prevents manual creation or deletion
    """
    serializer_class = DisposableIncomeBudgetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Returns the current user's budget for the current month.
        Creates a zero-value entry if one doesn't already exist.
        """
        user, start_of_month, end_of_month = get_user_and_month_range(
            self.request)
        month_start_date = start_of_month.date()

        # Auto-create budget if not present
        DisposableIncomeBudget.objects.get_or_create(
            owner=user,
            date=month_start_date,
            defaults={'amount': 0}
        )

        return DisposableIncomeBudget.objects.filter(
            owner=user,
            date=month_start_date,
        )

    def perform_create(self, serializer):
        """
        Block creation of budgets via POST. Budgets are auto-generated.
        """
        raise PermissionDenied("You cannot create a budget manually.")

    def destroy(self, request, *args, **kwargs):
        """
        Prevent users from deleting a budget.
        """
        raise PermissionDenied("You cannot delete a budget.")

    def get_object(self):
        obj = DisposableIncomeBudget.objects.get(pk=self.kwargs['pk'])

        if obj.owner != self.request.user:
            raise PermissionDenied(
                "You do not have permission to access this budget.")
        return obj
