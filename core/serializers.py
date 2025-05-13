import re
from django.contrib.auth.models import User
from rest_framework import serializers
from django.core.exceptions import ValidationError


class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer for updating or displaying user details.

    Includes validation for username constraints:
    - Alphanumeric with dashes/underscores
    - Max 40 characters
    - Case-insensitive uniqueness check
    """
    def validate_username(self, value):
        # 1. Allowed characters: letters, numbers, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise serializers.ValidationError(
                "Username can only contain letters, "
                "numbers, dashes (-), or underscores (_)."
            )

        # 2. Check length
        if len(value) > 40:
            raise serializers.ValidationError(
                "Username must be at most 40 characters.")

        # 3. Check uniqueness (case-insensitive)
        user_qs = User.objects.filter(username__iexact=value)
        if self.instance:
            user_qs = user_qs.exclude(pk=self.instance.pk)

        if user_qs.exists():
            raise serializers.ValidationError(
                "This username is already taken.")

        return value

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')


class ChangeEmailSerializer(serializers.Serializer):
    """
    Serializer for handling email change requests.

    Ensures the new email is valid and not already in use.
    """
    email = serializers.EmailField()

    def validate_email(self, value: str) -> str:
        # Ensure email is not already in use
        if User.objects.filter(email__iexact=value).exists():
            raise ValidationError("Email is already in use")
        return value
