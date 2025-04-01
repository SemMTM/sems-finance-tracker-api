from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from ..models.currency import Currency
from ..serializers.currency import CurrencySerializer


class CurrencyViewSet(viewsets.ViewSet):
    """
    Allows a user to view and update their currency preference.
    Ensures only one entry per user and restricts access to their own setting.
    """
    serializer_class = CurrencySerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """
        Return the user's currency, creating one if it doesn't exist.
        """
        obj, _ = Currency.objects.get_or_create(owner=request.user)
        serializer = CurrencySerializer(obj, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        obj = Currency.objects.filter(pk=pk, owner=request.user).first()
        if not obj:
            raise PermissionDenied("Not found or not your currency setting.")
        serializer = CurrencySerializer(obj, context={'request': request})
        return Response(serializer.data)

    def update(self, request, pk=None):
        obj = Currency.objects.filter(pk=pk, owner=request.user).first()
        if not obj:
            raise PermissionDenied("Not found or not your currency setting.")
        serializer = CurrencySerializer(
            obj, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request):
        return Response(
            {'detail': 'Currency settings are created automatically.'},
            status=405)
