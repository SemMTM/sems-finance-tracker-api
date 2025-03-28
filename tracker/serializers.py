from rest_framework import serializers
from .models import Expenditure


class ExpenditureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expenditure
        fields = [
            'id', 'owner', 'title', 'amount',
            'repeated', 'type', 'date',
            ]
