from core.utils.date_helpers import get_user_and_month_range
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from transactions.models import (
    Income, Expenditure, DisposableIncomeSpending, DisposableIncomeBudget)
from transactions.serializers.monthly_summary import MonthlySummarySerializer


class MonthlySummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 1. Get date range for the current month
        user, start_date, end_date = get_user_and_month_range(request)

        # 2. Fetch and sum incomes
        total_income = Income.objects.filter(
            owner=user,
            date__range=(start_date, end_date)
        ).aggregate(total=Sum('amount'))['total'] or 0

        # 3. Fetch and sum expenditures by type
        def get_expenditure_total(category):
            return Expenditure.objects.filter(
                owner=user,
                type=category,
                date__range=(start_date, end_date)
            ).aggregate(total=Sum('amount'))['total'] or 0

        bills_total = get_expenditure_total('BILL')
        saving_total = get_expenditure_total('SAVING')
        investment_total = get_expenditure_total('INVESTMENT')

        # 4. Get disposable income spending
        disposable_spending = DisposableIncomeSpending.objects.filter(
            owner=user,
            date__range=(start_date, end_date)
        ).aggregate(total=Sum('amount'))['total'] or 0

        # 5. Get budget for the month
        budget = DisposableIncomeBudget.objects.filter(
          owner=user,
          date__month=start_date.month,
          date__year=start_date.year
        ).first()
        budget_amount = budget.amount if budget else 0

        # 6. Calculate total and remaining disposable
        total = total_income - (
            bills_total + saving_total + investment_total + disposable_spending)
        remaining_disposable = budget_amount - disposable_spending

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
