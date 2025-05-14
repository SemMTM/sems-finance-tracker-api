from rest_framework import serializers
from ..models.currency import Currency
from core.utils.currency import get_currency_symbol


class CurrencySerializer(serializers.ModelSerializer):
    """
    Serializer for the Currency model, exposing symbol and display name.

    Includes:
    - Full display label from choices (e.g., 'British Pound £')
    - Raw currency symbol (e.g., '£')
    - Read-only owner
    - Boolean is_owner field for frontend UI logic
    """
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

    def get_is_owner(self, obj) -> bool:
        """
        Returns True if the requesting user is the owner of this currency.
        """
        request = self.context.get('request')
        return bool(request and request.user == obj.owner)

    def get_currency_display(self, obj) -> str:
        """
        Returns the full human-readable label from the model's choices.
        Example: 'GBP' -> 'British Pound £'
        """
        return obj.get_currency_display()

    def get_currency_symbol(self, obj) -> str:
        """
        Returns the raw currency symbol extracted from the code.
        Example: 'GBP' -> '£'
        """
        return get_currency_symbol(obj.currency)
