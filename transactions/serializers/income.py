from rest_framework import serializers
from ..models.income import Income


class IncomeSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    is_owner = serializers.SerializerMethodField()
    formatted_amount = serializers.SerializerMethodField()
    readable_date = serializers.SerializerMethodField()
    repeated_display = serializers.SerializerMethodField()

    class Meta:
        model = Income
        fields = [
            'id', 'title', 'amount', 'formatted_amount',
            'date', 'readable_date',
            'repeated', 'repeated_display',
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

    def get_repeated_display(self, obj):
        """
        Returns the human-readable display value for the 'repeated' field.
        """
        return obj.get_repeated_display()
