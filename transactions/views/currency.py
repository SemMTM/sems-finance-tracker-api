from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, MethodNotAllowed
from ..models.currency import Currency
from ..serializers.currency import CurrencySerializer


class CurrencyViewSet(viewsets.ViewSet):
    """
    ViewSet for managing a user's currency preference.
    - GET /currency/       → returns current user's currency
    - GET /currency/:id/   → returns only if it's the user's own currency
    - PUT /currency/:id/   → allows user to update their own currency
    - POST /currency/      → blocked; currency is auto-created
    """
    serializer_class = CurrencySerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request) -> Response:
        """
        Returns the authenticated user's currency object,
        creating it if it doesn't exist.
        """
        currency, _ = Currency.objects.get_or_create(owner=request.user)
        serializer = CurrencySerializer(currency, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, pk=None) -> Response:
        """
        Retrieve the user's currency by primary key.
        Only allowed if the object belongs to the current user.
        """
        currency = self._get_object_or_403(pk, request.user)
        serializer = CurrencySerializer(currency, context={'request': request})
        return Response(serializer.data)

    def update(self, request, pk=None) -> Response:
        """
        Update the user's currency preference.
        Only allowed if the object belongs to the current user.
        """
        currency = self._get_object_or_403(pk, request.user)
        serializer = CurrencySerializer(
            currency, data=request.data,
            partial=True, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request) -> Response:
        """
        Explicitly disallow creating currency via POST.
        """
        raise MethodNotAllowed("POST",
                               detail="Currency is created automatically.")

    def _get_object_or_403(self, pk, user) -> Currency:
        """
        Utility to fetch an object by pk and user, or raise PermissionDenied.
        """
        obj = Currency.objects.filter(pk=pk, owner=user).first()
        if not obj:
            raise PermissionDenied("Not found or not your currency setting.")
        return obj
