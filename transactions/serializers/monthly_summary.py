from rest_framework import serializers
from core.utils.currency import get_user_currency_symbol


class MonthlySummarySerializer(serializers.Serializer):
    formatted_income = serializers.SerializerMethodField()
    formatted_bills = serializers.SerializerMethodField()
    formatted_saving = serializers.SerializerMethodField()
    formatted_investment = serializers.SerializerMethodField()
    formatted_disposable_spending = serializers.SerializerMethodField()
    formatted_total = serializers.SerializerMethodField()
    formatted_budget = serializers.SerializerMethodField()
    formatted_remaining_disposable = serializers.SerializerMethodField()

    def get_symbol(self):
        request = self.context.get('request')
        return get_user_currency_symbol(request)

    def format_amount(self, amount):
        return f"{self.get_symbol()}{amount / 100:.2f}"

    def get_formatted_income(self, obj):
        return self.format_amount(obj['income'])

    def get_formatted_bills(self, obj):
        return self.format_amount(obj['bills'])

    def get_formatted_saving(self, obj):
        return self.format_amount(obj['saving'])

    def get_formatted_investment(self, obj):
        return self.format_amount(obj['investment'])

    def get_formatted_disposable_spending(self, obj):
        return self.format_amount(obj['disposable_spending'])

    def get_formatted_total(self, obj):
        return self.format_amount(obj['total'])

    def get_formatted_budget(self, obj):
        return self.format_amount(obj['budget'])

    def get_formatted_remaining_disposable(self, obj):
        return self.format_amount(obj['remaining_disposable'])
