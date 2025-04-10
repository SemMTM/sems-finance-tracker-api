from rest_framework import serializers
from ..models.expenditure import Expenditure
from decimal import Decimal
from core.utils.currency import get_user_currency_symbol


class ExpenditureSerializer(serializers.ModelSerializer):

    owner = serializers.ReadOnlyField(source='owner.username')
    is_owner = serializers.SerializerMethodField()
    formatted_amount = serializers.SerializerMethodField()
    readable_date = serializers.SerializerMethodField()
    repeated_display = serializers.SerializerMethodField()
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, write_only=True)

    class Meta:
        model = Expenditure
        fields = [
            'id',
            'title',
            'amount',
            'formatted_amount',
            'type',
            'repeated',
            'date',
            'readable_date',
            'owner',
            'is_owner',
            'repeated_display',
        ]
        read_only_fields = ['owner']

    def get_is_owner(self, obj):
        """
        Returns True if the logged-in user is the owner of the expenditure.
        """
        request = self.context.get('request')
        return request.user == obj.owner if request else False

    def get_formatted_amount(self, obj):
        symbol = get_user_currency_symbol(self.context.get('request'))
        return f"{symbol}{obj.amount / 100:.2f}"

    def get_readable_date(self, obj):
        """
        Returns a human-readable formatted date, e.g. "March 28, 2025".
        """
        return obj.date.strftime('%B %d, %Y')

    def get_repeated_display(self, obj):
        """
        Returns the human-readable display value for the 'repeated' field.
        """
        return obj.get_repeated_display()

    def to_internal_value(self, data):
        """
        Convert pounds (with decimals) to pence (int) before saving.
        """
        data = super().to_internal_value(data)
        data['amount'] = int(
            Decimal(data['amount']).quantize(Decimal('0.01')) * 100
        )
        return data
