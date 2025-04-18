from rest_framework import serializers
from ..models.disposable import (
    DisposableIncomeBudget, DisposableIncomeSpending)
from decimal import Decimal
from core.utils.currency import get_user_currency_symbol
from core.utils.date_helpers import get_user_and_month_range
from django.db.models import Sum


class DisposableIncomeBudgetSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    date = serializers.ReadOnlyField()
    is_owner = serializers.SerializerMethodField()
    formatted_amount = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()
    remaining_formatted = serializers.SerializerMethodField()
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, write_only=True)

    class Meta:
        model = DisposableIncomeBudget
        fields = ['id', 'amount', 'formatted_amount', 'owner', 'is_owner',
                  'date', 'remaining_amount', 'remaining_formatted']
        read_only_fields = ['owner']

    def get_is_owner(self, obj):
        request = self.context.get('request')
        return request.user == obj.owner if request else False

    def get_formatted_amount(self, obj):
        symbol = get_user_currency_symbol(self.context.get('request'))
        return f"{symbol}{obj.amount / 100:.2f}"

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
        request = self.context.get('request')
        user, start, end = get_user_and_month_range(request)

        total_spent = DisposableIncomeSpending.objects.filter(
            owner=user,
            date__gte=start,
            date__lt=end
        ).aggregate(total=Sum('amount'))['total'] or 0

        return obj.amount - total_spent

    def get_remaining_formatted(self, obj):
        remaining = self.get_remaining_amount(obj)
        symbol = get_user_currency_symbol(self.context.get('request'))
        value = abs(remaining) / 100
        sign = '-' if remaining < 0 else ''
        return f"{sign}{symbol}{value:.2f}"


class DisposableIncomeSpendingSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    is_owner = serializers.SerializerMethodField()
    formatted_amount = serializers.SerializerMethodField()
    readable_date = serializers.SerializerMethodField()
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, write_only=True)

    class Meta:
        model = DisposableIncomeSpending
        fields = [
            'id', 'title', 'amount', 'formatted_amount',
            'date', 'readable_date',
            'owner', 'is_owner'
        ]
        read_only_fields = ['owner']

    def get_is_owner(self, obj):
        request = self.context.get('request')
        return request.user == obj.owner if request else False

    def get_formatted_amount(self, obj):
        symbol = get_user_currency_symbol(self.context.get('request'))
        return f"{symbol}{obj.amount / 100:.2f}"

    def get_readable_date(self, obj):
        return obj.date.strftime('%B %d, %Y')

    def to_internal_value(self, data):
        """
        Convert pounds (with decimals) to pence (int) before saving.
        """
        data = super().to_internal_value(data)
        data['amount'] = int(
            Decimal(data['amount']).quantize(Decimal('0.01')) * 100
        )
        return data
