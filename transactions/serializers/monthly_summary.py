from rest_framework import serializers
from core.utils.currency import get_user_currency_symbol


class MonthlySummarySerializer(serializers.Serializer):
    """
    Serializer for returning a user's monthly financial summary,
    with all fields formatted as currency strings.
    """
    formatted_income = serializers.SerializerMethodField()
    formatted_bills = serializers.SerializerMethodField()
    formatted_saving = serializers.SerializerMethodField()
    formatted_investment = serializers.SerializerMethodField()
    formatted_disposable_spending = serializers.SerializerMethodField()
    formatted_total = serializers.SerializerMethodField()
    formatted_budget = serializers.SerializerMethodField()
    formatted_remaining_disposable = serializers.SerializerMethodField()

    def get_symbol(self) -> str:
        """
        Retrieves the user's preferred currency symbol from context.
        """
        request = self.context.get('request')
        return get_user_currency_symbol(request)

    def format_amount(self, amount) -> str:
        """
        Formats an integer amount (in pence) to a currency string.
        Handles negative values with a leading minus sign.
        Example: -1050 → "-£10.50"
        """
        symbol = self.get_symbol()
        value = abs(amount) / 100
        sign = '-' if amount < 0 else ''
        return f"{sign}{symbol}{value:.2f}"

    def get_formatted_income(self, obj) -> str:
        """Returns formatted total income."""
        return self.format_amount(obj.get('income', 0))

    def get_formatted_bills(self, obj) -> str:
        """Returns formatted total bills."""
        return self.format_amount(obj.get('bills', 0))

    def get_formatted_saving(self, obj) -> str:
        """Returns formatted total saving."""
        return self.format_amount(obj.get('saving', 0))

    def get_formatted_investment(self, obj) -> str:
        """Returns formatted total investment."""
        return self.format_amount(obj.get('investment', 0))

    def get_formatted_disposable_spending(self, obj) -> str:
        """Returns formatted disposable income spending."""
        return self.format_amount(obj.get('disposable_spending', 0))

    def get_formatted_total(self, obj) -> str:
        """Returns formatted total income minus all spending."""
        return self.format_amount(obj.get('total', 0))

    def get_formatted_budget(self, obj) -> str:
        """Returns formatted disposable income budget."""
        return self.format_amount(obj.get('budget', 0))

    def get_formatted_remaining_disposable(self, obj) -> str:
        """Returns formatted remaining disposable income after spending."""
        return self.format_amount(obj.get('remaining_disposable', 0))
