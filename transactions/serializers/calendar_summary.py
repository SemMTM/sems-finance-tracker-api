from rest_framework import serializers
from core.utils.currency import get_user_currency_symbol


class CalendarSummarySerializer(serializers.Serializer):
    date = serializers.DateField()
    formatted_income = serializers.SerializerMethodField()
    formatted_expenditure = serializers.SerializerMethodField()

    def get_formatted_income(self, obj):
        symbol = get_user_currency_symbol(self.context["request"])
        return f"{symbol}{obj['income'] / 100:.2f}"

    def get_formatted_expenditure(self, obj):
        symbol = get_user_currency_symbol(self.context["request"])
        return f"{symbol}{obj['expenditure'] / 100:.2f}"
