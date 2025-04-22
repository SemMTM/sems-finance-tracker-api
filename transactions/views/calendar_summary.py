from collections import defaultdict
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from transactions.models import Income, Expenditure, DisposableIncomeSpending
from transactions.serializers.calendar_summary import CalendarSummarySerializer
from core.utils.date_helpers import get_user_and_month_range


class CalendarSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 1. Get user and this month's date range
        user, start_of_month, end_of_month = get_user_and_month_range(request)

        # 2. Set up a daily income/expenditure tracker
        day_totals = defaultdict(lambda: {"income": 0, "expenditure": 0})

        # 3. Aggregate income by date
        incomes = Income.objects.filter(
            owner=user, date__gte=start_of_month, date__lt=end_of_month)
        for item in incomes:
            date_key = item.date.date().isoformat()
            day_totals[date_key]["income"] += item.amount

        # 4. Aggregate expenditure by date
        expenditures = Expenditure.objects.filter(
            owner=user, date__gte=start_of_month, date__lt=end_of_month)
        for item in expenditures:
            date_key = item.date.date().isoformat()
            day_totals[date_key]["expenditure"] += item.amount

        # Aggregate disposable spending
        disposable_spending = DisposableIncomeSpending.objects.filter(
            owner=user, date__gte=start_of_month, date__lt=end_of_month)
        for item in disposable_spending:
            date_key = item.date.date().isoformat()
            day_totals[date_key]["expenditure"] += item.amount

        # 5. Build a list of all days in the month
        result = []
        current = start_of_month
        while current < end_of_month:
            date_key = current.date().isoformat()
            result.append({
                "date": date_key,
                "income": day_totals[date_key]["income"],
                "expenditure": day_totals[date_key]["expenditure"]
            })
            current += timedelta(days=1)

        # 6. Serialize and return
        serializer = CalendarSummarySerializer(
            result, many=True, context={"request": request})
        return Response(serializer.data)
