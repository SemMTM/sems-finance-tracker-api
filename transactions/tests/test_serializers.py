from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.utils.timezone import now
from transactions.serializers.calendar_summary import CalendarSummarySerializer
from transactions.models.currency import Currency
from transactions.serializers.currency import CurrencySerializer
from transactions.models.disposable import (
    DisposableIncomeBudget,
    DisposableIncomeSpending
)
from transactions.serializers.disposable import (
    DisposableIncomeBudgetSerializer,
    DisposableIncomeSpendingSerializer
)
from transactions.models.expenditure import Expenditure
from transactions.serializers.expenditure import ExpenditureSerializer


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


class DisposableIncomeBudgetSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass")
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.request.user = self.user

        self.budget = DisposableIncomeBudget.objects.create(
            owner=self.user,
            amount=10000,  # £100
            date=now().replace(day=1)
        )

    def test_is_owner_true_when_user_matches(self):
        """
        Should return True for is_owner when request user matches budget owner.
        """
        serializer = DisposableIncomeBudgetSerializer(
            instance=self.budget, context={'request': self.request}
        )
        self.assertTrue(serializer.data['is_owner'])

    def test_remaining_amount_is_correct(self):
        """
        Should correctly calculate remaining amount from budget and spendings.
        """
        DisposableIncomeSpending.objects.create(
            owner=self.user,
            title='Snacks',
            amount=3000,  # £30
            date=now()
        )

        serializer = DisposableIncomeBudgetSerializer(
            instance=self.budget, context={'request': self.request}
        )
        self.assertEqual(serializer.data['remaining_amount'], 7000)  # 10000 - 3000

    def test_to_internal_value_converts_to_pence(self):
        """
        Should convert pounds to integer pence during deserialization.
        """
        serializer = DisposableIncomeBudgetSerializer(
            data={'amount': '50.50'}, context={'request': self.request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['amount'], 5050)


class DisposableIncomeSpendingSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass")
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.request.user = self.user

        self.spending = DisposableIncomeSpending.objects.create(
            owner=self.user,
            title="Lunch",
            amount=2500,  # £25.00
            date=now()
        )

    def test_is_owner_returns_true_for_request_user(self):
        """
        Should return True for is_owner when the request user matches the spending owner.
        """
        serializer = DisposableIncomeSpendingSerializer(
            instance=self.spending, context={"request": self.request}
        )
        self.assertTrue(serializer.data["is_owner"])

    def test_formatted_amount_includes_currency_symbol(self):
        """
        Should format the amount with the correct currency symbol and decimal places.
        """
        serializer = DisposableIncomeSpendingSerializer(
            instance=self.spending, context={"request": self.request}
        )
        self.assertEqual(serializer.data["formatted_amount"], "£25.00")

    def test_readable_date_returns_correct_format(self):
        """
        Should return a human-readable string date like 'May 15, 2025'.
        """
        serializer = DisposableIncomeSpendingSerializer(
            instance=self.spending, context={"request": self.request}
        )
        formatted = serializer.data["readable_date"]
        self.assertIn(str(self.spending.date.year), formatted)
        self.assertIn(self.spending.date.strftime("%B"), formatted)

    def test_to_internal_value_converts_to_pence(self):
        """
        Should convert a decimal pound string into integer pence when saving.
        """
        serializer = DisposableIncomeSpendingSerializer(
            data={
                "title": "Coffee",
                "amount": "3.75",
                "date": now().isoformat()
            },
            context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["amount"], 375)


class ExpenditureSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass")
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.request.user = self.user

        self.expenditure = Expenditure.objects.create(
            owner=self.user,
            title="Rent",
            amount=120000,  # £1,200.00
            type="BILL",
            repeated="MONTHLY",
            date=now()
        )

    def test_is_owner_returns_true_when_user_matches(self):
        """
        Should return True for is_owner when request user matches expenditure owner.
        """
        serializer = ExpenditureSerializer(
            instance=self.expenditure, context={'request': self.request}
        )
        self.assertTrue(serializer.data['is_owner'])

    def test_formatted_amount_includes_currency_symbol(self):
        """
        Should return formatted amount string with currency symbol and decimals.
        """
        serializer = ExpenditureSerializer(
            instance=self.expenditure, context={'request': self.request}
        )
        self.assertEqual(serializer.data['formatted_amount'], "£1200.00")

    def test_readable_date_is_formatted_properly(self):
        """
        Should return a readable date like 'May 15, 2025'.
        """
        serializer = ExpenditureSerializer(
            instance=self.expenditure, context={'request': self.request}
        )
        formatted = serializer.data['readable_date']
        self.assertIn(str(self.expenditure.date.year), formatted)
        self.assertIn(self.expenditure.date.strftime("%B"), formatted)

    def test_repeated_display_matches_model_choice(self):
        """
        Should return the human-readable label for the 'repeated' field.
        """
        serializer = ExpenditureSerializer(
            instance=self.expenditure, context={'request': self.request}
        )
        self.assertEqual(serializer.data['repeated_display'], "Monthly")

    def test_to_internal_value_converts_pounds_to_pence(self):
        """
        Should convert 'amount' from pounds to integer pence on input.
        """
        data = {
            'title': 'Utilities',
            'amount': '99.99',
            'type': 'BILL',
            'repeated': 'NEVER',
            'date': now().isoformat()
        }
        serializer = ExpenditureSerializer(
            data=data, context={'request': self.request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['amount'], 9999)
