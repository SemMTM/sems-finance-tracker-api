from rest_framework import serializers
from decimal import Decimal
from ..models.expenditure import Expenditure
from core.utils.currency import get_user_currency_symbol


class ExpenditureSerializer(serializers.ModelSerializer):
    """
    Serializer for a user's non-disposable expenditure entry.
    Converts amount input from pounds to pence and returns formatted output.
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
        help_text="Amount in pounds; will be converted to pence."
    )

    class Meta:
        model = Expenditure
        fields = [
            'id', 'title', 'amount', 'formatted_amount',
            'type', 'repeated', 'date', 'readable_date',
            'owner', 'is_owner', 'repeated_display',
        ]
        read_only_fields = ['owner']

    def get_is_owner(self, obj) -> bool:
        """
        Returns True if the logged-in user is the owner of the expenditure.
        """
        request = self.context.get('request')
        return bool(request and request.user == obj.owner)

    def get_formatted_amount(self, obj):
        symbol = get_user_currency_symbol(self.context.get('request'))
        return f"{symbol}{obj.amount / 100:.2f}"

    def get_readable_date(self, obj):
        """
        Returns a human-readable formatted date, e.g. "Mar 28 2025".
        """
        return obj.date.strftime('%B %d, %Y')

    def get_repeated_display(self, obj):
        """
        Returns the human-readable display value for the 'repeated' field.
        """
        return obj.get_repeated_display()

    def to_internal_value(self, data):
        """
        Converts incoming pound value (as Decimal) to integer pence
        before saving.
        """
        data = super().to_internal_value(data)
        data['amount'] = int(
            Decimal(data['amount']).quantize(Decimal('0.01')) * 100
        )
        return data
