from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from transactions.models import Income, Expenditure, DisposableIncomeSpending
from core.utils.date_helpers import get_weeks_in_month_clipped


class WeeklySummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 1. Get user and week ranges clipped to current month
        user, weeks, _, _ = get_weeks_in_month_clipped(request)

        weekly_data = []
        for week_start, week_end in weeks:
            # 2. Aggregate financial data in this week
            income = Income.objects.filter(
                owner=user,
                date__gte=week_start,
                date__lt=week_end
            ).aggregate(total=Sum('amount'))['total'] or 0

            expenditures = Expenditure.objects.filter(
                owner=user,
                date__gte=week_start,
                date__lt=week_end
            ).aggregate(total=Sum('amount'))['total'] or 0

            disposable = DisposableIncomeSpending.objects.filter(
                owner=user,
                date__gte=week_start,
                date__lt=week_end
            ).aggregate(total=Sum('amount'))['total'] or 0

            total_cost = expenditures + disposable
            summary = income - total_cost

            weekly_data.append({
                'week_start': week_start.date().isoformat(),
                'week_end': (week_end - timedelta(days=1)).date().isoformat(),
                'weekly_income': income,
                'weekly_cost': total_cost,
                'summary': summary,
            })

        return Response({
            'weeks': weekly_data
        })
