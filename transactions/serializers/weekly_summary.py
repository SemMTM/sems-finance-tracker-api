from rest_framework import serializers
from core.utils.currency import get_user_currency_symbol


class WeeklySummarySerializer(serializers.Serializer):
    """
    Serializer for summarizing a single week's income, cost, and net summary.
    All monetary values are returned as formatted currency strings.
    """
    week_start = serializers.CharField()
    week_end = serializers.CharField()
    income = serializers.SerializerMethodField()
    cost = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()

    def get_symbol(self):
        """
        Retrieves the user's preferred currency symbol
        from the request context.
        """
        request = self.context.get('request')
        return get_user_currency_symbol(request)

    def format_amount(self, amount: int) -> int:
        """
        Formats a pence integer into a currency string.
        Handles negative values with a leading minus sign.
        """
        symbol = self.get_symbol()
        value = abs(amount) / 100
        sign = '-' if amount < 0 else ''
        return f"{sign}{symbol}{value:.2f}"

    def get_income(self, obj) -> str:
        """
        Returns formatted weekly income.
        """
        return self.format_amount(obj.get('weekly_income', 0))

    def get_cost(self, obj) -> str:
        """
        Returns formatted weekly cost.
        """
        return self.format_amount(obj.get('weekly_cost', 0))

    def get_summary(self, obj) -> str:
        """
        Returns formatted weekly net summary (income - cost).
        """
        return self.format_amount(obj.get('summary', 0))
