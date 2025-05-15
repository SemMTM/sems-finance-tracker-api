from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from transactions.serializers.calendar_summary import CalendarSummarySerializer
from transactions.models.currency import Currency
from transactions.serializers.currency import CurrencySerializer


class CalendarSummarySerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass")
        Currency.objects.create(owner=self.user, currency='GBP')
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.request.user = self.user

        self.sample_data = {
            "date": "2025-10-03",
            "income": 12000,       # £120.00
            "expenditure": 4500    # £45.00
        }

    def test_income_is_formatted_correctly(self):
        """
        Should return income in pounds with two decimal places.
        """
        serializer = CalendarSummarySerializer(
            instance=self.sample_data,
            context={"request": self.request}
        )
        self.assertEqual(serializer.data["income"], "120.00")

    def test_expenditure_is_formatted_correctly(self):
        """
        Should return expenditure in pounds with two decimal places.
        """
        serializer = CalendarSummarySerializer(
            instance=self.sample_data,
            context={"request": self.request}
        )
        self.assertEqual(serializer.data["expenditure"], "45.00")

    def test_currency_symbol_is_correct_for_user(self):
        """
        Should return the correct currency symbol from user's settings.
        """
        serializer = CalendarSummarySerializer(
            instance=self.sample_data,
            context={"request": self.request}
        )
        self.assertEqual(serializer.data["currency_symbol"], "£")

    def test_missing_fields_default_to_zero(self):
        """
        Should handle missing 'income' or 'expenditure' by defaulting to 0.
        """
        partial_data = {"date": "2025-10-03"}  # no income or expenditure
        serializer = CalendarSummarySerializer(
            instance=partial_data,
            context={"request": self.request}
        )
        self.assertEqual(serializer.data["income"], "0.00")
        self.assertEqual(serializer.data["expenditure"], "0.00")


class CurrencySerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester',
                                             password='pass')
        self.other_user = User.objects.create_user(
            username='someone_else', password='pass')
        self.currency = Currency.objects.create(owner=self.user, currency='GBP')
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.request.user = self.user

    def test_owner_username_is_serialized(self):
        """
        Should serialize the owner's username as a read-only field.
        """
        serializer = CurrencySerializer(instance=self.currency,
                                        context={'request': self.request})
        self.assertEqual(serializer.data['owner'], 'tester')

    def test_is_owner_true_for_request_user(self):
        """
        Should return True for is_owner when request.user
        matches the currency owner.
        """
        serializer = CurrencySerializer(instance=self.currency, context={
            'request': self.request})
        self.assertTrue(serializer.data['is_owner'])

    def test_is_owner_false_for_other_user(self):
        """
        Should return False for is_owner when request.user does not match the
        currency owner.
        """
        other_request = self.factory.get('/')
        other_request.user = self.other_user
        serializer = CurrencySerializer(instance=self.currency,
                                        context={'request': other_request})
        self.assertFalse(serializer.data['is_owner'])

    def test_currency_display_value_is_correct(self):
        """
        Should return the correct display label from model choices.
        Example: 'British Pound £' for GBP.
        """
        serializer = CurrencySerializer(instance=self.currency,
                                        context={'request': self.request})
        self.assertEqual(serializer.data['currency_display'],
                         'British Pound £')

    def test_currency_symbol_is_correct(self):
        """
        Should return the correct symbol based on the currency code.
        Example: '£' for GBP.
        """
        serializer = CurrencySerializer(instance=self.currency,
                                        context={'request': self.request})
        self.assertEqual(serializer.data['currency_symbol'], '£')
