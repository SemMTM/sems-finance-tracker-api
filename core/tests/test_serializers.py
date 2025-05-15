from django.test import TestCase
from django.contrib.auth.models import User
from core.serializers import CustomUserSerializer, ChangeEmailSerializer


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
        Should raise error if the username exists (case-insensitive)
        for another user.
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


class ChangeEmailSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='tester',
            email='old@example.com',
            password='pass'
        )
        self.existing_email_user = User.objects.create_user(
            username='other',
            email='taken@example.com',
            password='pass'
        )

    def test_valid_email_change(self):
        """
        Should accept a new, unused email and pass validation.
        """
        data = {'email': 'newemail@example.com'}
        serializer = ChangeEmailSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['email'], data['email'])

    def test_email_already_taken(self):
        """
        Should raise a validation error if the email is already in use
        (case-insensitive check).
        """
        data = {'email': 'TAKEN@example.com'}
        serializer = ChangeEmailSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        self.assertIn('already in use', serializer.errors['email'][0])

    def test_invalid_email_format(self):
        """
        Should raise an error if the provided email is not a valid format.
        """
        data = {'email': 'not-an-email'}
        serializer = ChangeEmailSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
