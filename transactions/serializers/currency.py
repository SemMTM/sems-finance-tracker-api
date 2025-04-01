from rest_framework import serializers
from ..models.currency import Currency
from core.utils.currency import get_currency_symbol


class CurrencySerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    is_owner = serializers.SerializerMethodField()
    currency_display = serializers.SerializerMethodField()
    currency_symbol = serializers.SerializerMethodField()

    class Meta:
        model = Currency
        fields = [
            'id',
            'currency',
            'currency_display',
            'currency_symbol',
            'owner',
            'is_owner'
        ]
        read_only_fields = ['owner']

    def get_is_owner(self, obj):
        request = self.context.get('request')
        return request.user == obj.owner if request else False

    def get_currency_display(self, obj):
        """
        Returns the full human-readable label from the model's choices.
        Example: 'GBP' -> 'British Pound £'
        """
        return obj.get_currency_display()

    def get_currency_symbol(self, obj):
        """
        Returns just the currency symbol extracted from the display label.
        """
        return get_currency_symbol(obj.currency)
