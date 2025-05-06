from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import ChangeEmailSerializer
from dj_rest_auth.views import UserDetailsView
from core.utils.repeat_check import check_and_run_monthly_repeat


class ChangeEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        # Check if the user is authenticated
        user = request.user

        # Deserialize the request data and validate
        serializer = ChangeEmailSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user.email = email  # Update the email address
            user.save()  # Save the user object with the new email

            return Response(
                {"message": "Email updated successfully"},
                status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomUserDetailsView(UserDetailsView):
    def get(self, request, *args, **kwargs):
        check_and_run_monthly_repeat(request.user)
        return super().get(request, *args, **kwargs)
