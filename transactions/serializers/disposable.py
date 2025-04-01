from rest_framework import serializers
from ..models.disposable import (
    DisposableIncomeBudget, DisposableIncomeSpending)


class DisposableIncomeBudgetSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    is_owner = serializers.SerializerMethodField()
    formatted_amount = serializers.SerializerMethodField()

    class Meta:
        model = DisposableIncomeBudget
        fields = ['id', 'amount', 'formatted_amount', 'owner', 'is_owner']
        read_only_fields = ['owner']

    def get_is_owner(self, obj):
        request = self.context.get('request')
        return request.user == obj.owner if request else False

    def get_formatted_amount(self, obj):
        return f"£{obj.amount:.2f}"


class DisposableIncomeSpendingSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    is_owner = serializers.SerializerMethodField()
    formatted_amount = serializers.SerializerMethodField()
    readable_date = serializers.SerializerMethodField()

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
