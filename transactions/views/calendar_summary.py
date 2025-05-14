from collections import defaultdict
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from transactions.models import Income, Expenditure, DisposableIncomeSpending
from transactions.serializers.calendar_summary import CalendarSummarySerializer
from core.utils.date_helpers import get_user_and_month_range


class CalendarSummaryView(APIView):
    """
    API view that returns a daily summary of income and expenditure
    for the current or requested month. Used in the calendar view.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        # 1. Get user and this month's date range
        user, start_of_month, end_of_month = get_user_and_month_range(request)

        # 2. Set up a daily income/expenditure tracker
        day_totals = defaultdict(lambda: {"income": 0, "expenditure": 0})

        # 3. Preload financial records and aggregate by day
        self._aggregate_by_day(
            Income, "income", user, start_of_month, end_of_month, day_totals)
        self._aggregate_by_day(
            Expenditure, "expenditure", user, start_of_month,
            end_of_month, day_totals)
        self._aggregate_by_day(
            DisposableIncomeSpending, "expenditure", user,
            start_of_month, end_of_month, day_totals)

        # 4. Generate a list of daily summaries in order
        result = self._build_result(start_of_month, end_of_month, day_totals)

        # 5. Serialize and return the summary data
        serializer = CalendarSummarySerializer(
            result, many=True, context={"request": request})
        return Response(serializer.data)

    def _aggregate_by_day(
            self, model, field: str, user, start, end, day_totals):
        """
        Fetches records from a given model and adds daily totals
        to the day_totals dict using date keys.
        """
        records = model.objects.filter(
            owner=user, date__gte=start, date__lt=end)
        for item in records:
            date_key = item.date.date().isoformat()
            day_totals[date_key][field] += item.amount

    def _build_result(self, start, end, day_totals) -> list[dict]:
        """
        Constructs a list of daily income/expenditure summaries
        for serialization.
        """
        result = []
        current = start
        while current < end:
            date_key = current.date().isoformat()
            result.append({
                "date": date_key,
                "income": day_totals[date_key]["income"],
                "expenditure": day_totals[date_key]["expenditure"]
            })
            current += timedelta(days=1)
        return result
