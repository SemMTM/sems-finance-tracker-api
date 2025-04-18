from rest_framework import serializers
from core.utils.currency import get_user_currency_symbol


class WeeklySummarySerializer(serializers.Serializer):
    week_start = serializers.CharField()
    week_end = serializers.CharField()
    income = serializers.SerializerMethodField()
    cost = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()

    def get_symbol(self):
        request = self.context.get('request')
        return get_user_currency_symbol(request)

    def format_amount(self, amount):
        symbol = self.get_symbol()
        value = abs(amount) / 100
        sign = '-' if amount < 0 else ''
        return f"{sign}{symbol}{value:.2f}"

    def get_income(self, obj):
        return self.format_amount(obj['weekly_income'])

    def get_cost(self, obj):
        return self.format_amount(obj['weekly_cost'])

    def get_summary(self, obj):
        return self.format_amount(obj['summary'])
