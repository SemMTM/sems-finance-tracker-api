from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from unittest.mock import patch


class ChangeEmailViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='old@example.com',
            password='password123'
        )
        self.url = reverse('change_email')
        self.client.force_authenticate(user=self.user)

    def test_successful_email_update(self):
        """
        Should allow authenticated user to update email to a new, unused address.
        """
        response = self.client.put(self.url, {'email': 'new@example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'new@example.com')

    def test_reject_existing_email(self):
        """
        Should return 400 if the new email is already in use by another user.
        """
        User.objects.create_user(username='other', email='taken@example.com', password='pass')
        response = self.client.put(self.url, {'email': 'taken@example.com'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_invalid_email_format(self):
        """
        Should return 400 if the provided email format is invalid.
        """
        response = self.client.put(self.url, {'email': 'not-an-email'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_unauthenticated_user_cannot_update(self):
        """
        Should reject email change requests from unauthenticated users.
        """
        self.client.logout()
        response = self.client.put(self.url, {'email': 'new@example.com'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CustomUserDetailsViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='tester',
            email='user@example.com',
            password='pass123'
        )
        self.url = '/dj-rest-auth/user/'
        self.client.force_authenticate(user=self.user)

    @patch('core.views.check_and_run_monthly_repeat')
    def test_get_triggers_repeat_check_and_returns_user_data(self, mock_repeat):
        """
        Should trigger check_and_run_monthly_repeat when user details are requested.
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        mock_repeat.assert_called_once()

        # Check that user was passed as the second argument
        _, kwargs = mock_repeat.call_args
        self.assertEqual(mock_repeat.call_args[0][1], self.user)

    def test_unauthenticated_request_is_rejected(self):
        """
        Should return 403 if the user is not authenticated.
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
