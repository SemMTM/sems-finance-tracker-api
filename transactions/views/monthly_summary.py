from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from transactions.models import (
    Income,
    Expenditure,
    DisposableIncomeSpending,
    DisposableIncomeBudget
)
from transactions.serializers.monthly_summary import MonthlySummarySerializer
from core.utils.date_helpers import get_weeks_in_month_clipped


class MonthlySummaryView(APIView):
    """
    API view that returns a monthly summary of all financial categories
    (income, spending, saving, investment, and disposable tracking)
    for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        # 1. Extract user and date range
        user, weeks, start_date, end_date = get_weeks_in_month_clipped(request)

        # 2. Aggregate income total
        total_income = self._get_total(Income, user, start_date, end_date)

        # 3. Aggregate expenditures by type
        bills_total = self._get_total(
            Expenditure, user, start_date, end_date, type='BILL')
        saving_total = self._get_total(
            Expenditure, user, start_date, end_date, type='SAVING')
        investment_total = self._get_total(
            Expenditure, user, start_date, end_date, type='INVESTMENT')

        # 4. Get disposable income spending
        disposable_spending = self._get_total(
            DisposableIncomeSpending, user, start_date, end_date)

        # 5. Get budget for the month
        budget = DisposableIncomeBudget.objects.filter(
          owner=user,
          date__month=start_date.month,
          date__year=start_date.year
        ).first()
        budget_amount = budget.amount if budget else 0

        # 6. Summary calculations
        total = total_income - (
            bills_total + saving_total + investment_total +
            disposable_spending)
        remaining_disposable = budget_amount - disposable_spending

        # 7. Build and return formatted response
        raw_data = {
            'income': total_income,
            'bills': bills_total,
            'saving': saving_total,
            'investment': investment_total,
            'disposable_spending': disposable_spending,
            'total': total,
            'budget': budget_amount,
            'remaining_disposable': remaining_disposable,
        }
        serializer = MonthlySummarySerializer(
            raw_data, context={'request': request})
        return Response(serializer.data)

    def _get_total(self, model, user, start, end, **filters) -> int:
        """
        Aggregates the total 'amount' for a given model, user, and time range.
        Optionally filters by expenditure type.
        """
        return model.objects.filter(
            owner=user,
            date__gte=start,
            date__lt=end,
            **filters
        ).aggregate(total=Sum('amount')).get('total') or 0
