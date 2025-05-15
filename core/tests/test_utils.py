from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser, User
from transactions.models.currency import Currency
from core.utils.currency import get_currency_symbol, get_user_currency_symbol
from datetime import datetime
from django.utils.timezone import make_aware
from core.utils.date_helpers import (
    get_user_and_month_range,
    get_weeks_in_month_clipped
)


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


class DateHelpersTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='tester', password='testpass')

    def test_get_user_and_month_range_with_valid_param(self):
        """
        Returns correct start/end datetimes when a valid ?month=YYYY-MM param is provided.
        """
        request = self.factory.get('/?month=2025-09')
        request.user = self.user

        user, start, end = get_user_and_month_range(request)

        self.assertEqual(user, self.user)
        self.assertEqual(start, make_aware(datetime(2025, 9, 1, 0, 0)))
        self.assertEqual(end, make_aware(datetime(2025, 10, 1, 0, 0)))

    def test_get_user_and_month_range_with_invalid_param(self):
        """
        Falls back to current month when ?month= param is invalid.
        """
        request = self.factory.get('/?month=invalid')
        request.user = self.user

        user, start, end = get_user_and_month_range(request)

        self.assertEqual(user, self.user)
        self.assertEqual(start.day, 1)
        self.assertEqual(start.hour, 0)
        self.assertTrue(end > start)

    def test_get_user_and_month_range_without_param(self):
        """
        Returns current month when no ?month= param is provided.
        """
        request = self.factory.get('/')
        request.user = self.user

        user, start, end = get_user_and_month_range(request)

        self.assertEqual(user, self.user)
        self.assertEqual(start.day, 1)
        self.assertEqual(start.hour, 0)
        self.assertTrue(end > start)

    def test_get_weeks_in_month_clipped_structure(self):
        """
        Returns weekly (start, end) tuples clipped to within the month.
        """
        request = self.factory.get('/?month=2025-09')
        request.user = self.user

        user, weeks, start, end = get_weeks_in_month_clipped(request)

        self.assertEqual(user, self.user)
        self.assertEqual(start, make_aware(datetime(2025, 9, 1, 0, 0)))
        self.assertEqual(end, make_aware(datetime(2025, 10, 1, 0, 0)))
        self.assertGreaterEqual(len(weeks), 4)

        for start_week, end_week in weeks:
            self.assertLessEqual(start_week, end_week)
            self.assertLessEqual(end_week, end)
