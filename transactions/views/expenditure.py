from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from django.utils.timezone import now
from ..models.expenditure import Expenditure
from ..serializers.expenditure import ExpenditureSerializer


class ExpenditureViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenditureSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return this user's expenditures for the current month only.
        """
        user = self.request.user
        current_date = now()
        start_of_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if start_of_month.month == 12:
            end_of_month = start_of_month.replace(year=start_of_month.year + 1, month=1)
        else:
            end_of_month = start_of_month.replace(month=start_of_month.month + 1)

        return Expenditure.objects.filter(
            owner=user,
            date__gte=start_of_month,
            date__lt=end_of_month
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
