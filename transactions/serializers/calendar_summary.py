from rest_framework import serializers
from core.utils.currency import get_user_currency_symbol


class CalendarSummarySerializer(serializers.Serializer):
    """
    Serializer for calendar summary data, converting pence to formatted strings
    and appending the user's currency symbol from request context.
    """
    date = serializers.DateField()
    income = serializers.SerializerMethodField()
    expenditure = serializers.SerializerMethodField()
    currency_symbol = serializers.SerializerMethodField()

    def get_income(self, obj) -> str:
        """
        Returns the income formatted as a decimal string in pounds.
        """
        income_pence = obj.get("income", 0)
        return f"{income_pence / 100:.2f}"

    def get_expenditure(self, obj) -> str:
        """
        Returns the expenditure formatted as a decimal string in pounds.
        """
        expenditure_pence = obj.get("expenditure", 0)
        return f"{expenditure_pence / 100:.2f}"

    def get_currency_symbol(self, obj) -> str:
        """
        Returns the user's selected currency symbol from the request context.
        """
        request = self.context.get("request")
        return get_user_currency_symbol(request)
