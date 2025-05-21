from rest_framework import serializers
from django.db.models import Sum
from decimal import Decimal
from ..models.disposable import (
    DisposableIncomeBudget, DisposableIncomeSpending)
from core.utils.currency import get_user_currency_symbol
from core.utils.date_helpers import get_user_and_month_range


class DisposableIncomeBudgetSerializer(serializers.ModelSerializer):
    """
    Serializer for a user's disposable income budget for the current month.
    Includes calculated remaining balance and formatted currency output.
    """
    owner = serializers.ReadOnlyField(source='owner.username')
    date = serializers.ReadOnlyField()
    is_owner = serializers.SerializerMethodField()
    formatted_amount = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()
    remaining_formatted = serializers.SerializerMethodField()
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        write_only=True,
        help_text="Amount in pounds; will be stored in pence."
    )

    class Meta:
        model = DisposableIncomeBudget
        fields = [
            'id', 'amount', 'formatted_amount',
            'owner', 'is_owner', 'date',
            'remaining_amount', 'remaining_formatted'
        ]
        read_only_fields = ['owner']

    def get_is_owner(self, obj) -> bool:
        request = self.context.get('request')
        return bool(request and request.user == obj.owner)

    def to_internal_value(self, data):
        """
        Convert pounds (with decimals) to pence (int) before saving.
        """
        data = super().to_internal_value(data)
        data['amount'] = int(
            Decimal(data['amount']).quantize(Decimal('0.01')) * 100
        )
        return data

    def get_remaining_amount(self, obj):
        """
        Returns the remaining disposable income by subtracting
        spending from the budget within the same month.
        """
        request = self.context.get('request')
        if not request:
            return obj.amount

        user, start, end = get_user_and_month_range(request)
        total_spent = DisposableIncomeSpending.objects.filter(
            owner=user,
            date__gte=start,
            date__lt=end
        ).aggregate(total=Sum('amount'))['total'] or 0

        return obj.amount - total_spent

    def get_formatted_amount(self, obj) -> str:
        symbol = get_user_currency_symbol(self.context.get('request'))
        return f"{symbol}{obj.amount / 100:.2f}"

    def get_remaining_formatted(self, obj) -> str:
        remaining = self.get_remaining_amount(obj)
        symbol = get_user_currency_symbol(self.context.get('request'))
        value = abs(remaining) / 100
        sign = '-' if remaining < 0 else ''
        return f"{sign}{symbol}{value:.2f}"


class DisposableIncomeSpendingSerializer(serializers.ModelSerializer):
    """
    Serializer for a single spending entry deducted from
    a user's disposable income.
    Converts pounds to pence on input, and returns
    formatted amounts with currency symbols.
    """
    owner = serializers.ReadOnlyField(source='owner.username')
    is_owner = serializers.SerializerMethodField()
    formatted_amount = serializers.SerializerMethodField()
    readable_date = serializers.SerializerMethodField()
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        write_only=True,
        help_text="Amount in pounds; will be stored in pence."
    )

    class Meta:
        model = DisposableIncomeSpending
        fields = [
            'id', 'title', 'amount', 'formatted_amount',
            'date', 'readable_date',
            'owner', 'is_owner'
        ]
        read_only_fields = ['owner']

    def get_is_owner(self, obj) -> bool:
        request = self.context.get('request')
        return bool(request and request.user == obj.owner)

    def get_formatted_amount(self, obj) -> str:
        """
        Returns the amount formatted as a string with currency symbol.
        Example: £23.00
        """
        symbol = get_user_currency_symbol(self.context.get('request'))
        return f"{symbol}{obj.amount / 100:.2f}"

    def get_readable_date(self, obj) -> str:
        """
        Returns the date in a human-readable format.
        Example: "April 12, 2025"
        """
        return obj.date.strftime('%B %d, %Y')

    def to_internal_value(self, data):
        """
        Convert pounds (as decimal) to pence (as integer) before saving.
        """
        data = super().to_internal_value(data)
        data['amount'] = int(
            Decimal(data['amount']).quantize(Decimal('0.01')) * 100
        )
        return data

    def validate_amount(self, value):
        """
        Ensure amount is non-negative.
        """
        if value < 0:
            raise serializers.ValidationError("Amount cannot be negative.")
        return value
