from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from transactions.serializers.calendar_summary import CalendarSummarySerializer
from core.models import UserProfile
from transactions.models.currency import Currency


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
