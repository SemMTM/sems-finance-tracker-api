from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from django.utils.timezone import now
from transactions.models import (
    Income,
    Expenditure,
    DisposableIncomeSpending,
    Currency,
    DisposableIncomeBudget,
  )
from datetime import timedelta
from urllib.parse import urlencode
from dateutil.relativedelta import relativedelta
from rest_framework import status
from django.urls import reverse
from rest_framework.exceptions import MethodNotAllowed


class CalendarSummaryViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='tester', password='pass')
        self.client.force_authenticate(user=self.user)
        self.today = now().replace(hour=0, minute=0, second=0, microsecond=0)

    def test_multiple_entries_across_days(self):
        """Should separate totals by day and return both in results."""
        day_1 = self.today
        day_2 = self.today + timedelta(days=1)

        Income.objects.create(
            owner=self.user, title='Day 1', amount=10000, date=day_1)
        Income.objects.create(
            owner=self.user, title='Day 2', amount=5000, date=day_2)

        response = self.client.get('/calendar-summary/')
        self.assertEqual(response.status_code, 200)

        data = {d['date']: d['income'] for d in response.data}
        self.assertEqual(data[day_1.date().isoformat()], '100.00')
        self.assertEqual(data[day_2.date().isoformat()], '50.00')

    def test_returns_zero_for_days_with_no_data(self):
        """Should still return 0.00 income/expenditure
        for days without entries."""
        yesterday = self.today - timedelta(days=1)
        Income.objects.create(
            owner=self.user, title='Bonus', amount=5000, date=yesterday)

        response = self.client.get('/calendar-summary/')
        today_data = next((
            d for d in response.data if d["date"] == self.today.date(
            ).isoformat()), None)

        self.assertIsNotNone(today_data)
        self.assertEqual(today_data["income"], "0.00")
        self.assertEqual(today_data["expenditure"], "0.00")

    def test_handles_month_param_correctly(self):
        """Should return only results for specified month
        if ?month=YYYY-MM is used."""
        other_month = self.today - relativedelta(months=1)
        Income.objects.create(
            owner=self.user, title='Old Entry', amount=9999, date=other_month)

        params = urlencode({'month': self.today.strftime("%Y-%m")})
        response = self.client.get(f'/calendar-summary/?{params}')
        self.assertEqual(response.status_code, 200)

        for entry in response.data:
            self.assertTrue(entry['date'].startswith(self.today.strftime(
                "%Y-%m")))

    def test_invalid_month_param_falls_back_to_current(self):
        """Should gracefully fall back to current month if month
        param is invalid."""
        Income.objects.create(
            owner=self.user, title='Salary', amount=8888, date=self.today)

        response = self.client.get('/calendar-summary/?month=invalid')
        self.assertEqual(response.status_code, 200)
        dates = [d['date'] for d in response.data]
        self.assertIn(self.today.date().isoformat(), dates)

    def test_returns_all_zeros_when_no_data(self):
        """Should return 0.00 income/expenditure
        for every day if no entries exist."""
        response = self.client.get('/calendar-summary/')
        self.assertEqual(response.status_code, 200)

        for day in response.data:
            self.assertEqual(day["income"], "0.00")
            self.assertEqual(day["expenditure"], "0.00")

    def test_correctly_aggregates_all_sources(self):
        """Should aggregate income, expenditure,
        and disposable spending per day."""
        day = self.today
        Income.objects.create(
            owner=self.user, title='Job', amount=10000, date=day)
        Expenditure.objects.create(
            owner=self.user, title='Bill', amount=3000, date=day)
        DisposableIncomeSpending.objects.create(
            owner=self.user, title='Coffee', amount=200, date=day)

        response = self.client.get('/calendar-summary/')
        self.assertEqual(response.status_code, 200)

        entry = next((
            d for d in response.data if d["date"] == day.date().isoformat()),
            None)
        self.assertIsNotNone(entry)
        self.assertEqual(entry["income"], "100.00")
        self.assertEqual(entry["expenditure"], "32.00")

    def test_response_is_chronological(self):
        """Should return the results ordered by date ascending."""
        Income.objects.create(owner=self.user, title='Old',
                              amount=5000, date=self.today)
        Income.objects.create(owner=self.user, title='New',
                              amount=7000, date=self.today + timedelta(days=2))

        response = self.client.get('/calendar-summary/')
        self.assertEqual(response.status_code, 200)

        dates = [d['date'] for d in response.data]
        self.assertEqual(dates, sorted(dates))

    def test_requires_authentication(self):
        """
        Should return 401 Unauthorized if user is not authenticated.
        """
        self.client.logout()
        response = self.client.get('/calendar-summary/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CurrencyViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='user1',
                                             password='testpass')
        self.user2 = User.objects.create_user(username='user2',
                                              password='testpass')
        self.client.force_authenticate(user=self.user)
        self.currency = Currency.objects.create(owner=self.user,
                                                currency='USD')
        self.currency_url = f'/currency/{self.currency.pk}/'

    def test_list_creates_currency_if_not_exists(self):
        """Should auto-create and return a currency if one doesn't exist."""
        Currency.objects.filter(owner=self.user).delete()
        response = self.client.get('/currency/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['owner'], self.user.username)

    def test_list_returns_existing_currency(self):
        """Should return the existing currency for authenticated user."""
        response = self.client.get('/currency/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['currency'], self.currency.currency)

    def test_retrieve_own_currency(self):
        """Should allow user to retrieve their own currency via pk."""
        response = self.client.get(self.currency_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['currency'], self.currency.currency)

    def test_retrieve_other_users_currency_raises_permission_denied(self):
        """Should not allow user to access another user's currency."""
        other_currency = Currency.objects.create(
            owner=self.user2, currency='EUR')
        response = self.client.get(f'/currency/{other_currency.pk}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_own_currency(self):
        """Should allow user to update their own currency setting."""
        response = self.client.put(self.currency_url, {'currency': 'GBP'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['currency'], 'GBP')
        self.currency.refresh_from_db()
        self.assertEqual(self.currency.currency, 'GBP')

    def test_update_other_users_currency_fails(self):
        """Should block users from updating another user's currency."""
        other_currency = Currency.objects.create(
            owner=self.user2, currency='AUD')
        response = self.client.put(
            f'/currency/{other_currency.pk}/', {'currency': 'JPY'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        other_currency.refresh_from_db()
        self.assertEqual(other_currency.currency, 'AUD')

    def test_create_method_is_disallowed(self):
        """Should raise MethodNotAllowed for POST to /currency/."""
        response = self.client.post('/currency/', {'currency': 'USD'})
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(
            response.data['detail'], "Currency is created automatically.")

    def test_requires_authentication(self):
        """Should return 403 for unauthenticated
        access to currency endpoints."""
        self.client.logout()
        response = self.client.get('/currency/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DisposableIncomeBudgetViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='budgetuser', password='pass')
        self.client.force_authenticate(user=self.user)
        self.url = '/disposable-budget/'

    def test_auto_creates_budget_if_not_exists(self):
        """Should automatically create a 0-value budget
        for the current month on GET."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            DisposableIncomeBudget.objects.filter(owner=self.user).count(), 1)
        self.assertEqual(response.data[0]['formatted_amount'], '£0.00')

    def test_retrieves_existing_budget(self):
        """Should return the already existing budget if one exists."""
        today = now().date().replace(day=1)
        DisposableIncomeBudget.objects.create(
            owner=self.user, amount=12000, date=today)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['formatted_amount'], '£120.00')

    def test_restricts_access_to_own_budget(self):
        """Should not allow access to other users' budgets."""
        other_user = User.objects.create_user(
            username='otheruser', password='pass')
        today = now().date().replace(day=1)
        budget = DisposableIncomeBudget.objects.create(
            owner=other_user, amount=15000, date=today)

        response = self.client.get(f'{self.url}{budget.pk}/')
        self.assertEqual(response.status_code, 403)

    def test_blocks_manual_create(self):
        """Should return 403 when trying to create a budget manually."""
        response = self.client.post(self.url, {
            'amount': 200,
            'date': now().date().isoformat()
        })
        self.assertEqual(response.status_code, 403)

    def test_blocks_budget_deletion(self):
        """Should return 403 when trying to delete a budget."""
        today = now().date().replace(day=1)
        budget = DisposableIncomeBudget.objects.create(
            owner=self.user, amount=20000, date=today)
        response = self.client.delete(f'{self.url}{budget.pk}/')
        self.assertEqual(response.status_code, 403)

    def test_requires_authentication(self):
        """Should return 403 if unauthenticated user accesses budget."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DisposableIncomeSpendingViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="pass")
        self.client.force_authenticate(user=self.user)
        self.url = "/disposable-spending/"
        self.today = now().replace(hour=0, minute=0, second=0, microsecond=0)

    def test_create_entry_sets_owner(self):
        """Should assign the logged-in user as the owner of new entries."""
        payload = {
            "title": "Takeaway",
            "amount": "12.50",
            "date": self.today.isoformat()
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        entry = DisposableIncomeSpending.objects.get()
        self.assertEqual(entry.owner, self.user)
        self.assertEqual(entry.amount, 1250)

    def test_user_only_sees_own_entries_for_current_month(self):
        """Should only return this user's entries for the current month."""
        DisposableIncomeSpending.objects.create(
            owner=self.user, title="Food", amount=1000, date=self.today)
        other_user = User.objects.create_user(
            username="other", password="pass")
        DisposableIncomeSpending.objects.create(
            owner=other_user, title="Coffee", amount=500, date=self.today)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Food")

    def test_filtering_with_month_param(self):
        """Should allow filtering by ?month=YYYY-MM to scope by month."""
        last_month = self.today - relativedelta(months=1)
        DisposableIncomeSpending.objects.create(
            owner=self.user, title="Old Purchase", amount=500, date=last_month)
        params = urlencode({"month": self.today.strftime("%Y-%m")})
        response = self.client.get(f"{self.url}?{params}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_user_cannot_access_others_entries(self):
        """Should forbid access to another user's entry by ID."""
        other_user = User.objects.create_user(
            username="otheruser", password="pass")
        entry = DisposableIncomeSpending.objects.create(
            owner=other_user, title="Hidden", amount=1000, date=self.today)

        response = self.client.get(f"{self.url}{entry.pk}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_delete_others_entry(self):
        """Should forbid deleting an entry not owned by user."""
        other_user = User.objects.create_user(
            username="someone", password="pass")
        entry = DisposableIncomeSpending.objects.create(
            owner=other_user, title="Nope", amount=500, date=self.today)
        response = self.client.delete(f"{self.url}{entry.pk}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_requires_authentication(self):
        """Should reject unauthenticated access to endpoints."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_blank_title_rejected(self):
        """Should reject entries with blank titles."""
        payload = {
            "title": "",
            "amount": "10.00",
            "date": self.today.isoformat()
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn('title', response.data)

    def test_negative_amount_rejected(self):
        """Should reject entries with negative amount input."""
        payload = {
            "title": "Invalid",
            "amount": "-10.00",
            "date": self.today.isoformat()
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_user_cannot_partial_update_foreign_entry(self):
        """Should prevent partial updates to entries not owned by the user."""
        other_user = User.objects.create_user(username="stranger", password="pass")
        entry = DisposableIncomeSpending.objects.create(
            owner=other_user, title="Hacked", amount=500, date=self.today)

        response = self.client.patch(f"{self.url}{entry.pk}/", {
            "title": "Updated"
        }, format="json")

        self.assertEqual(response.status_code, 403)

    def test_user_can_update_own_entry(self):
        """Should allow user to update their own entry."""
        entry = DisposableIncomeSpending.objects.create(
            owner=self.user, title="Lunch", amount=1000, date=self.today)
        payload = {
            "title": "Dinner",
            "amount": "20.00",
            "date": self.today.isoformat()
        }
        response = self.client.put(f"{self.url}{entry.pk}/", payload, format="json")
        self.assertEqual(response.status_code, 200)
        entry.refresh_from_db()
        self.assertEqual(entry.title, "Dinner")
        self.assertEqual(entry.amount, 2000)
