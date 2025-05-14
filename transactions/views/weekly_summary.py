from datetime import timedelta
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from transactions.models import Income, Expenditure, DisposableIncomeSpending
from core.utils.date_helpers import get_weeks_in_month_clipped
from transactions.serializers.weekly_summary import WeeklySummarySerializer


class WeeklySummaryView(APIView):
    """
    Returns a list of weekly financial summaries for the current or#
    selected month,
    including total income, combined costs, and net difference per week.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 1. Get user and week ranges clipped to current month
        user, weeks, _, _ = get_weeks_in_month_clipped(request)

        weekly_data = []
        for week_start, week_end in weeks:
            # 2. Aggregate financial data in this week
            income = self._get_total(
                Income, user, week_start, week_end)
            expenditures = self._get_total(
                Expenditure, user, week_start, week_end)
            disposable = self._get_total(
                DisposableIncomeSpending, user, week_start, week_end)

            total_cost = expenditures + disposable
            summary = income - total_cost

            weekly_data.append({
                'week_start': week_start.date().isoformat(),
                'week_end': (week_end - timedelta(days=1)).date().isoformat(),
                'weekly_income': income,
                'weekly_cost': total_cost,
                'summary': summary,
            })

        serializer = WeeklySummarySerializer(
            weekly_data, many=True, context={'request': request})
        return Response({'weeks': serializer.data})

    def _get_total(self, model, user, start, end) -> int:
        """
        Returns the sum of 'amount' for the given model, user, and date range.
        """
        return model.objects.filter(
            owner=user,
            date__gte=start,
            date__lt=end
        ).aggregate(total=Sum('amount')).get('total') or 0
