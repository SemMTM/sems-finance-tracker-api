from django.contrib.auth.models import User
from rest_framework import serializers
import re


class CustomUserSerializer(serializers.ModelSerializer):
    def validate_username(self, value):
        # 1. Check for valid characters
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise serializers.ValidationError(
                "Username can only contain letters, " \
                "numbers, dashes (-), or underscores (_)."
            )

        # 2. Check length
        if len(value) > 40:
            raise serializers.ValidationError(
                "Username must be at most 40 characters.")

        # 3. Check uniqueness (case-insensitive)
        if User.objects.filter(username__iexact=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("This username is already taken.")

        return value

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
