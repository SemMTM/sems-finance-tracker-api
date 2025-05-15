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
from transactions.models.income import Income
from transactions.serializers.income import IncomeSerializer
from transactions.serializers.monthly_summary import MonthlySummarySerializer
from transactions.serializers.weekly_summary import WeeklySummarySerializer


class CalendarSummarySerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester",
                                             password="pass")
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
        self.currency = Currency.objects.create(owner=self.user,
                                                currency='GBP')
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
        self.user = User.objects.create_user(username="tester",
                                             password="pass")
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
        Should correctly calculate remaining amount from budget
        and spendings.
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
        self.assertEqual(serializer.data['remaining_amount'], 7000)
        # 10000 - 3000

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
        self.user = User.objects.create_user(username="tester",
                                             password="pass")
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
        Should return True for is_owner when the request user
        matches the spending owner.
        """
        serializer = DisposableIncomeSpendingSerializer(
            instance=self.spending, context={"request": self.request}
        )
        self.assertTrue(serializer.data["is_owner"])

    def test_formatted_amount_includes_currency_symbol(self):
        """
        Should format the amount with the correct currency symbol
        and decimal places.
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
        self.user = User.objects.create_user(username="tester",
                                             password="pass")
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
        Should return True for is_owner when request user matches
        expenditure owner.
        """
        serializer = ExpenditureSerializer(
            instance=self.expenditure, context={'request': self.request}
        )
        self.assertTrue(serializer.data['is_owner'])

    def test_formatted_amount_includes_currency_symbol(self):
        """
        Should return formatted amount string with currency symbol
        and decimals.
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


class IncomeSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester",
                                             password="pass")
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.request.user = self.user

        self.income = Income.objects.create(
            owner=self.user,
            title="Salary",
            amount=250000,  # £2,500.00
            repeated="MONTHLY",
            date=now()
        )

    def test_is_owner_returns_true_for_matching_user(self):
        """
        Should return True when the request user matches the income owner.
        """
        serializer = IncomeSerializer(
            instance=self.income,
            context={"request": self.request}
        )
        self.assertTrue(serializer.data["is_owner"])

    def test_formatted_amount_includes_currency(self):
        """
        Should return formatted amount string with currency symbol.
        """
        serializer = IncomeSerializer(
            instance=self.income,
            context={"request": self.request}
        )
        self.assertEqual(serializer.data["formatted_amount"], "£2500.00")

    def test_readable_date_formatting_is_correct(self):
        """
        Should return a human-readable formatted date string.
        """
        serializer = IncomeSerializer(
            instance=self.income,
            context={"request": self.request}
        )
        formatted = serializer.data["readable_date"]
        self.assertIn(str(self.income.date.year), formatted)
        self.assertIn(self.income.date.strftime("%B"), formatted)

    def test_repeated_display_matches_model_label(self):
        """
        Should return the human-readable version of the repeated field.
        """
        serializer = IncomeSerializer(
            instance=self.income,
            context={"request": self.request}
        )
        self.assertEqual(serializer.data["repeated_display"], "Monthly")

    def test_to_internal_value_converts_to_pence(self):
        """
        Should convert decimal string pound input into integer pence.
        """
        data = {
            "title": "Freelance",
            "amount": "99.99",
            "date": now().isoformat(),
            "repeated": "NEVER"
        }
        serializer = IncomeSerializer(
            data=data, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["amount"], 9999)


class MonthlySummarySerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester',
                                             password='pass')
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.request.user = self.user

        self.sample_data = {
            'income': 50000,               # £500.00
            'bills': 20000,                # £200.00
            'saving': 5000,                # £50.00
            'investment': 5000,            # £50.00
            'disposable_spending': 10000,  # £100.00
            'total': 10000,                # £100.00
            'budget': 15000,               # £150.00
            'remaining_disposable': 5000   # £50.00
        }

    def test_all_fields_format_correctly(self):
        """
        Should return all formatted fields with currency symbol
        and 2 decimal places.
        """
        serializer = MonthlySummarySerializer(
            instance=self.sample_data,
            context={'request': self.request}
        )
        data = serializer.data

        self.assertEqual(data['formatted_income'], '£500.00')
        self.assertEqual(data['formatted_bills'], '£200.00')
        self.assertEqual(data['formatted_saving'], '£50.00')
        self.assertEqual(data['formatted_investment'], '£50.00')
        self.assertEqual(data['formatted_disposable_spending'], '£100.00')
        self.assertEqual(data['formatted_total'], '£100.00')
        self.assertEqual(data['formatted_budget'], '£150.00')
        self.assertEqual(data['formatted_remaining_disposable'], '£50.00')

    def test_negative_values_show_leading_minus(self):
        """
        Should include a minus sign before the symbol for negative values.
        """
        negative_data = self.sample_data.copy()
        negative_data['total'] = -2500  # -£25.00

        serializer = MonthlySummarySerializer(
            instance=negative_data,
            context={'request': self.request}
        )
        self.assertEqual(serializer.data['formatted_total'], '-£25.00')


class WeeklySummarySerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester",
                                             password="pass")
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.request.user = self.user

        self.week_data = {
            'week_start': '2025-05-01',
            'week_end': '2025-05-07',
            'weekly_income': 30000,   # £300.00
            'weekly_cost': 10000,     # £100.00
            'summary': 20000          # £200.00
        }

    def test_weekly_fields_are_formatted_correctly(self):
        """
        Should format income, cost, and summary with currency symbol.
        """
        serializer = WeeklySummarySerializer(
            instance=self.week_data,
            context={'request': self.request}
        )
        data = serializer.data

        self.assertEqual(data['income'], '£300.00')
        self.assertEqual(data['cost'], '£100.00')
        self.assertEqual(data['summary'], '£200.00')

    def test_negative_summary_has_leading_minus(self):
        """
        Should include a minus sign if summary is negative.
        """
        negative_data = self.week_data.copy()
        negative_data['summary'] = -5000  # -£50.00

        serializer = WeeklySummarySerializer(
            instance=negative_data,
            context={'request': self.request}
        )
        self.assertEqual(serializer.data['summary'], '-£50.00')
