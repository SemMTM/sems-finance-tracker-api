from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from dj_rest_auth.views import UserDetailsView
from .serializers import ChangeEmailSerializer
from core.utils.repeat_check import check_and_run_monthly_repeat


class ChangeEmailView(APIView):
    """
    Allows an authenticated user to change their email address.

    Validates input using ChangeEmailSerializer and ensures
    the email is not already in use.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs) -> Response:
        serializer = ChangeEmailSerializer(data=request.data)
        if serializer.is_valid():
            request.user.email = serializer.validated_data['email']
            request.user.save(update_fields=["email"])

            return Response(
                {"message": "Email updated successfully"},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomUserDetailsView(UserDetailsView):
    """
    Custom user detail view that also triggers monthly repeat checks
    for the authenticated user upon GET.
    """
    def get(self, request, *args, **kwargs) -> Response:
        check_and_run_monthly_repeat(request.user)
        return super().get(request, *args, **kwargs)
