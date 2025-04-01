from rest_framework import serializers
from ..models.disposable import (
    DisposableIncomeBudget, DisposableIncomeSpending)
from decimal import Decimal


class DisposableIncomeBudgetSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    is_owner = serializers.SerializerMethodField()
    formatted_amount = serializers.SerializerMethodField()
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, write_only=True)

    class Meta:
        model = DisposableIncomeBudget
        fields = ['id', 'amount', 'formatted_amount', 'owner', 'is_owner']
        read_only_fields = ['owner']

    def get_is_owner(self, obj):
        request = self.context.get('request')
        return request.user == obj.owner if request else False

    def get_formatted_amount(self, obj):
        return f"£{obj.amount / 100:.2f}"

    def to_internal_value(self, data):
        """
        Convert pounds (with decimals) to pence (int) before saving.
        """
        data = super().to_internal_value(data)
        data['amount'] = int(
            Decimal(data['amount']).quantize(Decimal('0.01')) * 100
        )
        return data


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
        return f"£{obj.amount / 100:.2f}"

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
