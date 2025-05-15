from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser, User
from transactions.models.currency import Currency
from core.utils.currency import get_currency_symbol, get_user_currency_symbol
from datetime import datetime
from unittest.mock import patch
from django.utils.timezone import make_aware, now
from core.utils.date_helpers import (
    get_user_and_month_range,
    get_weeks_in_month_clipped
)
from core.utils.repeat_check import check_and_run_monthly_repeat
from core.models import UserProfile


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


class CheckAndRunMonthlyRepeatTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='tester', password='pass')
        self.request = self.factory.get('/')
        self.request.user = self.user

    @patch("core.utils.repeat_check.generate_6th_month_repeats")
    @patch("core.utils.repeat_check.clean_old_transactions")
    def test_creates_profile_and_runs_repeat_if_not_run_this_month(self, mock_clean, mock_repeat):
        """
        Should create a UserProfile and run both repeat generators
        and cleanup when no repeat has been recorded for the current month.
        """
        check_and_run_monthly_repeat(self.request, self.user)

        profile = UserProfile.objects.get(user=self.user)
        current_month = now().date().replace(day=1)

        self.assertEqual(profile.last_repeat_check, current_month)
        self.assertEqual(mock_repeat.call_count, 2)
        mock_clean.assert_called_once_with(self.user)

    @patch("core.utils.repeat_check.generate_6th_month_repeats")
    @patch("core.utils.repeat_check.clean_old_transactions")
    def test_does_not_repeat_if_already_ran_this_month(self, mock_clean, mock_repeat):
        """
        Should not trigger repeat logic again if it was already run
        for the current month.
        """
        current_month = now().date().replace(day=1)

        UserProfile.objects.update_or_create(
            user=self.user,
            defaults={"last_repeat_check": current_month}
        )

        check_and_run_monthly_repeat(self.request, self.user)

        mock_repeat.assert_not_called()
        mock_clean.assert_not_called()

    @patch("core.utils.repeat_check.generate_6th_month_repeats")
    @patch("core.utils.repeat_check.clean_old_transactions")
    def test_runs_repeat_if_last_check_was_previous_month(self, mock_clean, mock_repeat):
        """
        Should trigger repeat logic if the last check was from a previous month.
        """
        previous_month = now().date().replace(day=1)
        if previous_month.month == 1:
            previous_month = previous_month.replace(year=previous_month.year - 1, month=12)
        else:
            previous_month = previous_month.replace(month=previous_month.month - 1)

        UserProfile.objects.update_or_create(
            user=self.user,
            defaults={"last_repeat_check": previous_month}
        )

        check_and_run_monthly_repeat(self.request, self.user)

        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.last_repeat_check, now().date().replace(day=1))
        self.assertEqual(mock_repeat.call_count, 2)
        mock_clean.assert_called_once_with(self.user)
