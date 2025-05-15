from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User


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
