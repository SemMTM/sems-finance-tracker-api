from rest_framework import serializers
from core.utils.currency import get_user_currency_symbol


class CalendarSummarySerializer(serializers.Serializer):
    date = serializers.DateField()
    income = serializers.SerializerMethodField()
    expenditure = serializers.SerializerMethodField()
    currency_symbol = serializers.SerializerMethodField()

    def get_income(self, obj):
        return f"{obj['income'] / 100:.2f}"

    def get_expenditure(self, obj):
        return f"{obj['expenditure'] / 100:.2f}"

    def get_currency_symbol(self, obj):
        return get_user_currency_symbol(self.context["request"])
