from django.test import TestCase
from django.contrib.auth.models import User
from core.serializers import CustomUserSerializer


class CustomUserSerializerTests(TestCase):
    def setUp(self):
        self.existing_user = User.objects.create_user(
            username='existing_user',
            email='existing@example.com',
            password='password'
        )

    def test_valid_username(self):
        """
        Should validate successfully with a clean, unique, valid username.
        """
        serializer = CustomUserSerializer(
            instance=self.existing_user,
            data={
                'username': 'valid_user',
                'email': 'new@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        self.assertTrue(serializer.is_valid())

    def test_invalid_username_characters(self):
        """
        Should raise error if the username contains invalid characters.
        """
        serializer = CustomUserSerializer(
            instance=self.existing_user,
            data={'username': 'invalid!name'}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)
        self.assertIn('contain only letters', serializer.errors['username'][0])

    def test_username_too_long(self):
        """
        Should raise error if the username exceeds 40 characters.
        """
        long_username = 'a' * 41
        serializer = CustomUserSerializer(
            instance=self.existing_user,
            data={'username': long_username}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)
        self.assertIn('at most 40 characters', serializer.errors['username'][0])

    def test_username_case_insensitive_duplicate(self):
        """
        Should raise error if the username exists (case-insensitive) for another user.
        """
        User.objects.create_user(username='TakenName')

        serializer = CustomUserSerializer(
            instance=self.existing_user,
            data={'username': 'takenname'}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)
        self.assertIn('already taken', serializer.errors['username'][0])

    def test_username_can_stay_the_same(self):
        """
        Should pass validation if the username is unchanged.
        """
        serializer = CustomUserSerializer(
            instance=self.existing_user,
            data={'username': 'existing_user'}
        )
        self.assertTrue(serializer.is_valid())
