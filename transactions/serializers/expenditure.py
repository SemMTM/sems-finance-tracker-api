from rest_framework import serializers
from ..models.expenditure import Expenditure


class ExpenditureSerializer(serializers.ModelSerializer):

    owner = serializers.ReadOnlyField(source='owner.username')
    is_owner = serializers.SerializerMethodField()
    formatted_amount = serializers.SerializerMethodField()
    readable_date = serializers.SerializerMethodField()

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
            'is_owner'
        ]
        read_only_fields = ['owner']

    def get_is_owner(self, obj):
        """
        Returns True if the logged-in user is the owner of the expenditure.
        """
        request = self.context.get('request')
        return request.user == obj.owner if request else False

    def get_formatted_amount(self, obj):
        """
        Returns a nicely formatted currency string, e.g. "£120.00".
        """
        return f"£{obj.amount:.2f}"

    def get_readable_date(self, obj):
        """
        Returns a human-readable formatted date, e.g. "March 28, 2025".
        """
        return obj.date.strftime('%B %d, %Y')
