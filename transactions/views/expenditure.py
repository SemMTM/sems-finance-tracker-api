from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from ..models.expenditure import Expenditure
from ..serializers.expenditure import ExpenditureSerializer
from core.utils.date_helpers import get_user_and_month_range
from ..utils import generate_weekly_repeats


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

        if instance.repeated == 'WEEKLY':
            generate_weekly_repeats(instance)

    def get_object(self):
        """
        Ensures the user only accesses their own object.
        """
        obj = super().get_object()
        if obj.owner != self.request.user:
            raise PermissionDenied(
                "You do not have permission to access this expenditure.")
        return obj

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Check if it's part of a repeat group
        if instance.repeated == 'WEEKLY' and instance.repeat_group_id:
            # Delete this instance and all future ones in the same group
            Expenditure.objects.filter(
                owner=request.user,
                repeat_group_id=instance.repeat_group_id,
                date__gte=instance.date
            ).delete()
            return Response(status=204)

        # Otherwise, just delete the single instance
        return super().destroy(request, *args, **kwargs)
