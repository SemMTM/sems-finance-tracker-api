from rest_framework import serializers
from decimal import Decimal
from ..models.income import Income
from core.utils.currency import get_user_currency_symbol


class IncomeSerializer(serializers.ModelSerializer):
    """
    Serializer for a user's income entry.
    Converts input from pounds to pence and provides formatted outputs for display.
    """
    owner = serializers.ReadOnlyField(source='owner.username')
    is_owner = serializers.SerializerMethodField()
    formatted_amount = serializers.SerializerMethodField()
    readable_date = serializers.SerializerMethodField()
    repeated_display = serializers.SerializerMethodField()
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        write_only=True,
        help_text="Amount in pounds; stored internally in pence."
    )

    class Meta:
        model = Income
        fields = [
            'id', 'title', 'amount', 'formatted_amount',
            'date', 'readable_date',
            'repeated', 'repeated_display',
            'owner', 'is_owner'
        ]
        read_only_fields = ['owner']

    def get_is_owner(self, obj) -> bool:
        """
        Returns True if the current user is the owner of the income entry.
        """
        request = self.context.get('request')
        return bool(request and request.user == obj.owner)

    def get_formatted_amount(self, obj) -> str:
        """
        Returns the income amount formatted as a currency string.
        Example: £1,200.00
        """
        symbol = get_user_currency_symbol(self.context.get('request'))
        return f"{symbol}{obj.amount / 100:.2f}"

    def get_readable_date(self, obj):
        """
        Returns the date in a readable format (e.g., Mar 25, 2025).
        """
        return obj.date.strftime('%B %d, %Y')

    def get_repeated_display(self, obj):
        """
        Returns the human-readable display value for the 'repeated' field.
        """
        return obj.get_repeated_display()

    def to_internal_value(self, data):
        """
        Convert pounds (as Decimal) to integer pence before saving to
        the database.
        """
        data = super().to_internal_value(data)
        data['amount'] = int(
            Decimal(data['amount']).quantize(Decimal('0.01')) * 100
        )
        return data
