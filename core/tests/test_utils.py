from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser, User
from transactions.models.currency import Currency
from core.utils.currency import get_currency_symbol, get_user_currency_symbol


class CurrencyUtilsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='tester', password='testpass')

    def test_get_currency_symbol_known_codes(self):
        """
        Should return the correct symbol for known currency codes,
        regardless of lowercase or uppercase input.
        """
        self.assertEqual(get_currency_symbol('usd'), '$')
        self.assertEqual(get_currency_symbol('EUR'), '€')
        self.assertEqual(get_currency_symbol('inr'), '₹')

    def test_get_currency_symbol_unknown_code(self):
        """
        Should return an empty string for unknown or unsupported currency codes.
        """
        self.assertEqual(get_currency_symbol('XYZ'), '')

    def test_get_user_currency_symbol_unauthenticated_user(self):
        """
        Should return the default currency symbol (GBP) if the user is unauthenticated.
        """
        request = self.factory.get('/')
        request.user = AnonymousUser()
        self.assertEqual(get_user_currency_symbol(request), '£')  # Default is GBP

    def test_get_user_currency_symbol_authenticated_without_currency(self):
        """
        Should return the default currency symbol (GBP) if the user is authenticated
        but has no currency entry set.
        """
        request = self.factory.get('/')
        request.user = self.user
        self.assertEqual(get_user_currency_symbol(request), '£')

    def test_get_user_currency_symbol_authenticated_with_currency(self):
        """
        Should return the user's selected currency symbol (e.g., JPY)
        if the user has an associated Currency model entry.
        """
        Currency.objects.create(owner=self.user, currency='JPY')
        request = self.factory.get('/')
        request.user = self.user
        self.assertEqual(get_user_currency_symbol(request), '¥')