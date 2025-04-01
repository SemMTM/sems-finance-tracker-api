from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from django.utils.timezone import now
from ..models.disposable import DisposableIncomeBudget
from ..serializers.disposable import DisposableIncomeBudgetSerializer
from core.utils.date_helpers import get_user_and_month_range


class DisposableIncomeBudgetViewSet(viewsets.ModelViewSet):
    """
    Auto-creates a 0-value budget for the current month on access.
    Only one budget per user per month.
    """
    serializer_class = DisposableIncomeBudgetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user, start_of_month, end_of_month = get_user_and_month_range(
            self.request)

        # Auto-create budget if not present
        obj, created = DisposableIncomeBudget.objects.get_or_create(
            owner=user,
            date__gte=start_of_month,
            date__lt=end_of_month,
            defaults={'amount': 0, 'date': now()}
        )
        return DisposableIncomeBudget.objects.filter(
            owner=user,
            date__gte=start_of_month,
            date__lt=end_of_month
        )

    def perform_create(self, serializer):
        raise PermissionDenied("You cannot create a budget manually.")

    def get_object(self):
        # Ensures user can only access their own budget
        obj = super().get_object()
        if obj.owner != self.request.user:
            raise PermissionDenied(
                "You do not have permission to access this budget.")
        return obj

    def update(self, request, *args, **kwargs):
        # Optional: enforce that amount can only be edited, not deleted
        if 'amount' in request.data:
            try:
                val = int(request.data['amount'])
                if val < 0:
                    raise PermissionDenied("Budget cannot be negative.")
            except ValueError:
                raise PermissionDenied("Invalid value for amount.")
        return super().update(request, *args, **kwargs)
