from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from ..models.expenditure import Expenditure
from ..serializers.expenditure import ExpenditureSerializer
from core.utils.date_helpers import get_user_and_month_range


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
        serializer.save(owner=self.request.user)

    def get_object(self):
        """
        Ensures the user only accesses their own object.
        """
        obj = super().get_object()
        if obj.owner != self.request.user:
            raise PermissionDenied(
                "You do not have permission to access this expenditure.")
        return obj
