from rest_framework import ViewSets, permissions
from .models import Expenditure
from .serializers import ExpenditureSerializer


class ExpenditureViewSet(ViewSets.ModelViewSet):
    serializer_class = ExpenditureSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Expenditure.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
