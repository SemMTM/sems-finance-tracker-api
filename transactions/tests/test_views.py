import uuid
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from django.utils.timezone import now, make_aware
from transactions.models import (
    Income,
    Expenditure,
    DisposableIncomeSpending,
    Currency,
    DisposableIncomeBudget,
  )
from datetime import timedelta, datetime
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

    def test_budget_not_duplicated_on_multiple_access(self):
        """Should only create one budget even with multiple accesses."""
        response1 = self.client.get("/disposable-budget/")
        response2 = self.client.get("/disposable-budget/")
        count = DisposableIncomeBudget.objects.filter(owner=self.user).count()
        self.assertEqual(count, 1)


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
        other_user = User.objects.create_user(
            username="stranger", password="pass")
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
        response = self.client.put(
            f"{self.url}{entry.pk}/", payload, format="json")
        self.assertEqual(response.status_code, 200)
        entry.refresh_from_db()
        self.assertEqual(entry.title, "Dinner")
        self.assertEqual(entry.amount, 2000)


class ExpenditureViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', password='pass')
        self.other_user = User.objects.create_user(
            username='other', password='pass')
        self.client.force_authenticate(user=self.user)
        self.url = '/expenditures/'
        self.today = make_aware(datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0))

    def test_create_expenditure_successfully(self):
        """Should allow authenticated user to create a single expenditure."""
        data = {
            'title': 'Rent',
            'amount': 100.00,
            'type': 'BILL',
            'date': self.today.date(),
            'repeated': 'NEVER'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Expenditure.objects.filter(
            owner=self.user, title='Rent').exists())

    def test_expenditure_requires_authentication(self):
        """Should reject requests from unauthenticated users with 403."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_access_others_expenditure(self):
        """Should return 403 when accessing another user's expenditure."""
        other_exp = Expenditure.objects.create(
            owner=self.other_user, title='Hidden', amount=1000,
            type='BILL', date=self.today
        )
        response = self.client.get(f'{self.url}{other_exp.pk}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_weekly_repeat_generates_future_entries(self):
        """Should auto-generate multiple future entries for weekly repeat."""
        data = {
            'title': 'Gym',
            'amount': 25.00,
            'type': 'BILL',
            'date': self.today.date(),
            'repeated': 'WEEKLY'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 201)
        group_id = Expenditure.objects.first().repeat_group_id
        count = Expenditure.objects.filter(repeat_group_id=group_id).count()
        self.assertTrue(count > 1)

    def test_update_repeated_entry_propagates(self):
        """Should update all future entries in group if date is unchanged."""
        initial = Expenditure.objects.create(
            owner=self.user, title='Sub', amount=1000, type='BILL',
            date=self.today, repeated='WEEKLY', repeat_group_id=uuid.uuid4()
        )
        future = Expenditure.objects.create(
            owner=self.user, title='Sub', amount=1000, type='BILL',
            date=self.today + timedelta(days=7), repeated='WEEKLY',
            repeat_group_id=initial.repeat_group_id
        )
        response = self.client.put(f'{self.url}{initial.pk}/', {
            'title': 'New Title',
            'amount': 50.00,
            'type': 'BILL',
            'date': initial.date.date(),
            'repeated': 'WEEKLY'
        }, format='json')
        future.refresh_from_db()
        self.assertEqual(future.title, 'New Title')
        self.assertEqual(future.amount, 5000)

    def test_delete_repeated_entry_removes_future_instances(self):
        """Should delete the current and future entries in the repeat group."""
        group_id = uuid.uuid4()
        base = Expenditure.objects.create(
            owner=self.user, title='Sub', amount=1000, type='BILL',
            date=self.today, repeated='MONTHLY', repeat_group_id=group_id
        )
        future = Expenditure.objects.create(
            owner=self.user, title='Sub', amount=1000, type='BILL',
            date=self.today + timedelta(days=30), repeated='MONTHLY',
            repeat_group_id=group_id
        )
        response = self.client.delete(f'{self.url}{base.pk}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Expenditure.objects.filter(
            repeat_group_id=group_id).exists())

    def test_get_queryset_limits_to_current_user_and_month(self):
        """Should only return this user's expenditures for the current month."""
        Expenditure.objects.create(owner=self.user, title='Valid',
                                   amount=1000, type='BILL', date=self.today)
        Expenditure.objects.create(owner=self.other_user, title='Invalid',
                                   amount=1000, type='BILL', date=self.today)
        response = self.client.get(self.url)
        titles = [e['title'] for e in response.data]
        self.assertIn('Valid', titles)
        self.assertNotIn('Invalid', titles)

    def test_list_returns_user_entries_only(self):
        """Should exclude other users' entries in the expenditure list."""
        Expenditure.objects.create(
            owner=self.user, title="My Expense", amount=1000,
            date=self.today)
        other_user = User.objects.create_user(username="intruder",
                                              password="hack")
        Expenditure.objects.create(owner=other_user, title="Their Expense",
                                   amount=9999, date=self.today)
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "My Expense")

    def test_create_adds_owner_and_generates_repeats(self):
        """Should assign owner and create repeated entries if applicable."""
        payload = {
            "title": "Gym",
            "amount": "10.00",
            "type": "BILL",
            "repeated": "WEEKLY",
            "date": self.today.date().isoformat(),
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertGreater(Expenditure.objects.filter(
            title="Gym", owner=self.user).count(), 1)

    def test_retrieve_rejects_unauthorized_access(self):
        """Should return 403 when trying to retrieve someone else's data."""
        entry = Expenditure.objects.create(
            owner=self.other_user, title="Private", amount=1000,
            date=self.today)
        response = self.client.get(f"{self.url}{entry.pk}/")
        self.assertEqual(response.status_code, 403)

    def test_partial_update_does_not_affect_unrelated_entries(self):
        """Should update only targeted entry, not other repeat groups."""
        entry = Expenditure.objects.create(
            owner=self.user, title="A", amount=1000, repeated="WEEKLY",
            repeat_group_id=uuid.uuid4(), date=self.today
        )
        Expenditure.objects.create(
            owner=self.user, title="B", amount=2000, repeated="WEEKLY",
            repeat_group_id=uuid.uuid4(), date=self.today + timedelta(weeks=1)
        )
        update = {"title": "Updated A"}
        response = self.client.patch(f"{self.url}{entry.pk}/", update)
        self.assertEqual(response.status_code, 200)

    def test_future_entries_updated_on_edit(self):
        """Should apply changes to current and future entries in repeat group."""
        group_id = uuid.uuid4()
        base = Expenditure.objects.create(
            owner=self.user, title="Old", amount=1000, repeated="WEEKLY",
            repeat_group_id=group_id, date=self.today
        )
        Expenditure.objects.create(
            owner=self.user, title="Old", amount=1000, repeated="WEEKLY",
            repeat_group_id=group_id, date=self.today + timedelta(days=7)
        )
        update = {
            "title": "New Title",
            "amount": "15.00",
            "type": "BILL",
            "repeated": "WEEKLY",
            "date": self.today.date().isoformat()
        }
        response = self.client.put(f"{self.url}{base.pk}/", update)
        self.assertEqual(response.status_code, 200)
        updated = Expenditure.objects.filter(title="New Title")
        self.assertGreater(len(updated), 1)

    def test_delete_non_repeated_deletes_only_one(self):
        """Should delete a one-off expenditure without affecting others."""
        entry = Expenditure.objects.create(
            owner=self.user, title="One-off", amount=1000, date=self.today)
        response = self.client.delete(f"{self.url}{entry.pk}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Expenditure.objects.filter(pk=entry.pk).exists())

    def test_delete_repeated_deletes_future_group(self):
        """Should remove current and future entries if repeated."""
        group_id = uuid.uuid4()
        base = Expenditure.objects.create(
            owner=self.user, title='Rent', amount=10000, repeated='WEEKLY',
            date=self.today, type='BILL', repeat_group_id=group_id
        )
        Expenditure.objects.create(
            owner=self.user, title='Rent', amount=10000, repeated='WEEKLY',
            date=self.today + timedelta(days=7), type='BILL',
            repeat_group_id=group_id
        )
        response = self.client.delete(f"{self.url}{base.pk}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Expenditure.objects.filter(
            repeat_group_id=group_id).exists())

    def test_invalid_update_returns_400(self):
        """Should reject invalid update with status code 400."""
        entry = Expenditure.objects.create(
            owner=self.user, title="Original", amount=1000, date=self.today)
        bad_update = {"amount": "-99.99"}
        response = self.client.put(f"{self.url}{entry.pk}/", bad_update)
        self.assertEqual(response.status_code, 400)

    def test_create_with_invalid_currency_format_fails(self):
        """Should return 400 when submitted amount format is invalid."""
        payload = {
            "title": "Bad Entry",
            "amount": "invalid",
            "type": "BILL",
            "repeated": "NONE",
            "date": self.today.date().isoformat(),
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_anonymous_user_cannot_access_view(self):
        """Should reject unauthenticated access to expenditure endpoint."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)


class IncomeViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='user1',
                                             password='pass')
        self.other_user = User.objects.create_user(
            username='user2', password='pass')
        self.client.force_authenticate(self.user)
        self.url = '/income/'
        self.today = make_aware(datetime.today())
        self.today_date = self.today.date()

    def test_authenticated_user_can_create_income(self):
        """Should allow authenticated users to create an income entry."""
        data = {
            'title': 'Salary',
            'amount': 150.00,
            'date': self.today_date,
            'repeated': 'NEVER'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Income.objects.filter(
            owner=self.user, title='Salary').exists())

    def test_unauthenticated_user_cannot_access(self):
        """Should reject unauthenticated requests with a 403 response."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_access_others_income(self):
        """Should return 403 if user tries to access another user's income."""
        other_entry = Income.objects.create(
            owner=self.other_user,
            title='Hacked',
            amount=10000,
            date=self.today
        )
        response = self.client.get(f"{self.url}{other_entry.pk}/")
        self.assertEqual(response.status_code, 403)

    def test_repeat_weekly_generates_additional_entries(self):
        """Should generate weekly repeated income entries up to 6 months."""
        data = {
            'title': 'Weekly Pay',
            'amount': 100.00,
            'repeated': 'WEEKLY',
            'date': self.today_date
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 201)
        group_id = Income.objects.first().repeat_group_id
        self.assertTrue(Income.objects.filter(
            repeat_group_id=group_id).count() > 1)

    def test_user_can_delete_all_future_group(self):
        """Should delete current and future entries in a repeat group."""
        group_id = uuid.uuid4()
        base = Income.objects.create(
            owner=self.user, title='Repeat', amount=1000,
            repeated='MONTHLY', repeat_group_id=group_id, date=self.today
        )
        future = Income.objects.create(
            owner=self.user, title='Repeat', amount=1000,
            repeated='MONTHLY', repeat_group_id=group_id,
            date=self.today + timedelta(days=30)
        )

        response = self.client.delete(f"{self.url}{base.pk}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Income.objects.filter(
            repeat_group_id=group_id).exists())

    def test_user_can_update_income_and_propagates(self):
        """Should update income and apply changes to future repeated entries."""
        group_id = uuid.uuid4()
        base = Income.objects.create(
            owner=self.user, title="Old", amount=1000,
            date=self.today, repeated="WEEKLY", repeat_group_id=group_id
        )
        future = Income.objects.create(
            owner=self.user, title="Old", amount=1000,
            date=self.today + timedelta(days=7),
            repeated="WEEKLY", repeat_group_id=group_id
        )

        payload = {
            "title": "New Title",
            "amount": "50.00",
            "date": base.date,
            "repeated": "WEEKLY"
        }

        response = self.client.put(
            f"{self.url}{base.pk}/", payload, format='json')
        self.assertEqual(response.status_code, 200)

        future.refresh_from_db()
        self.assertEqual(future.title, "New Title")
        self.assertEqual(future.amount, 5000)

    def test_invalid_update_returns_400(self):
        """Should return 400 when trying to update with invalid data."""
        entry = Income.objects.create(
            owner=self.user, title="Job", amount=1000, date=self.today
        )
        payload = {"amount": "-99.99"}
        response = self.client.put(f"{self.url}{entry.pk}/", payload)
        self.assertEqual(response.status_code, 400)

    def test_list_shows_only_current_month_entries(self):
        """Should only return entries from the current month for the user."""
        Income.objects.create(
            owner=self.user, title="Current", amount=1000, date=self.today
        )
        Income.objects.create(
            owner=self.user, title="Old", amount=1000,
            date=self.today - timedelta(days=45)
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        titles = [entry["title"] for entry in response.data]
        self.assertIn("Current", titles)
        self.assertNotIn("Old", titles)

    def test_user_cannot_create_income_for_another_user(self):
        """Should ignore owner field in payload
        and always assign logged-in user."""
        attacker = User.objects.create_user(
            username='attacker', password='hack')
        data = {
            'title': 'Malicious Income',
            'amount': 100.00,
            'date': self.today.date(),
            'repeated': 'NEVER',
            'owner': attacker.pk  # Should be ignored
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 201)
        income = Income.objects.get(title='Malicious Income')
        self.assertEqual(income.owner, self.user)

    def test_partial_update_single_field(self):
        """Should allow PATCH to update a single field."""
        entry = Income.objects.create(
            owner=self.user, title='Original', amount=1000, date=self.today)
        response = self.client.patch(
            f"{self.url}{entry.pk}/", {'title': 'Updated'})
        self.assertEqual(response.status_code, 200)
        entry.refresh_from_db()
        self.assertEqual(entry.title, 'Updated')

    def test_update_invalid_amount_format(self):
        """Should return 400 if amount is invalid."""
        entry = Income.objects.create(
            owner=self.user, title='Bad Format', amount=1000, date=self.today)
        response = self.client.put(
            f"{self.url}{entry.pk}/", {
            'title': 'Invalid',
            'amount': 'not-a-number',
            'date': self.today.date(),
            'repeated': 'NEVER'
            })
        self.assertEqual(response.status_code, 400)

    def test_repeat_monthly_generates_entries(self):
        """Should auto-generate entries for monthly repeated income."""
        data = {
            'title': 'Retainer',
            'amount': 200.00,
            'date': self.today.date(),
            'repeated': 'MONTHLY'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 201)
        group_id = Income.objects.first().repeat_group_id
        self.assertTrue(Income.objects.filter(
            repeat_group_id=group_id).count() > 1)

    def test_group_update_changes_repeat_group_id(self):
        """Should assign new group ID on update of repeated entry."""
        group_id = uuid.uuid4()
        entry = Income.objects.create(
            owner=self.user, title='GID Test', amount=1000,
            repeated='WEEKLY', repeat_group_id=group_id, date=self.today)

        response = self.client.put(f"{self.url}{entry.pk}/", {
            'title': 'GID Updated',
            'amount': '60.00',
            'date': entry.date,
            'repeated': 'WEEKLY'
        })

        entry.refresh_from_db()
        self.assertNotEqual(entry.repeat_group_id, group_id)

    def test_accessing_nonexistent_entry_returns_403(self):
        """Should return 403 instead of leaking 404 if entry isn't owned."""
        other_user = User.objects.create_user(
            username='hacker', password='pass')
        other_entry = Income.objects.create(
            owner=other_user, title='Invisible', amount=1000, date=self.today)
        response = self.client.get(f"{self.url}{other_entry.pk}/")
        self.assertEqual(response.status_code, 403)

    def test_can_retrieve_own_income_entry(self):
        """Should allow user to retrieve their own income."""
        entry = Income.objects.create(
            owner=self.user, title='Retrievable', amount=999, date=self.today)
        response = self.client.get(f"{self.url}{entry.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], 'Retrievable')

    def test_future_only_updated_on_group_edit(self):
        """Should update only future entries in repeat group, not past."""
        group_id = uuid.uuid4()
        past = Income.objects.create(
            owner=self.user, title='Past', amount=1000,
            repeated='WEEKLY', repeat_group_id=group_id,
            date=self.today - timedelta(weeks=1))
        current = Income.objects.create(
            owner=self.user, title='Current', amount=1000,
            repeated='WEEKLY', repeat_group_id=group_id,
            date=self.today)
        future = Income.objects.create(
            owner=self.user, title='Future', amount=1000,
            repeated='WEEKLY', repeat_group_id=group_id,
            date=self.today + timedelta(weeks=1))

        response = self.client.put(f"{self.url}{current.pk}/", {
            'title': 'Updated Title',
            'amount': '77.00',
            'date': current.date,
            'repeated': 'WEEKLY'
        })

        self.assertEqual(response.status_code, 200)
        past.refresh_from_db()
        future.refresh_from_db()
        self.assertEqual(past.title, 'Past')
        self.assertEqual(future.title, 'Updated Title')
        self.assertEqual(future.amount, 7700)


class MonthlySummaryViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', password='pass')
        self.other_user = User.objects.create_user(
            username='testuser2', password='pass')
        self.client.force_authenticate(self.user)
        self.url = '/monthly-summary/'
        self.today = make_aware(datetime.today())

    def test_returns_correct_aggregated_totals(self):
        """Should return correct totals for each financial category"""
        # Setup
        Income.objects.create(owner=self.user, title="Salary",
                              amount=100000, date=self.today)
        Expenditure.objects.create(owner=self.user, title="Rent",
                                   amount=50000, type="BILL", date=self.today)
        Expenditure.objects.create(owner=self.user, title="Save",
                                   amount=10000, type="SAVING",
                                   date=self.today)
        Expenditure.objects.create(owner=self.user, title="Invest",
                                   amount=5000, type="INVESTMENT",
                                   date=self.today)
        DisposableIncomeSpending.objects.create(owner=self.user,
                                                title="Coffee",
                                                amount=1500, date=self.today)
        DisposableIncomeBudget.objects.create(owner=self.user,
                                              amount=10000, date=self.today)

        # Action
        response = self.client.get(self.url)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["formatted_income"], "£1000.00")
        self.assertEqual(response.data["formatted_bills"], "£500.00")
        self.assertEqual(response.data["formatted_saving"], "£100.00")
        self.assertEqual(response.data["formatted_investment"], "£50.00")
        self.assertEqual(
            response.data["formatted_disposable_spending"], "£15.00")
        self.assertEqual(response.data["formatted_total"], "£335.00")
        self.assertEqual(response.data["formatted_budget"], "£100.00")
        self.assertEqual(
            response.data["formatted_remaining_disposable"], "£85.00")

    def test_returns_zero_when_no_entries_exist(self):
        """Should return 0.00 for all categories when no data exists"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["formatted_income"], "£0.00")
        self.assertEqual(response.data["formatted_bills"], "£0.00")
        self.assertEqual(response.data["formatted_saving"], "£0.00")
        self.assertEqual(response.data["formatted_investment"], "£0.00")
        self.assertEqual(
            response.data["formatted_disposable_spending"], "£0.00")
        self.assertEqual(response.data["formatted_total"], "£0.00")
        self.assertEqual(response.data["formatted_budget"], "£0.00")
        self.assertEqual(
            response.data["formatted_remaining_disposable"], "£0.00")

    def test_only_current_month_data_is_counted(self):
        """Should only include entries from the current month"""
        past_date = self.today - timedelta(days=40)

        # Add older data
        Income.objects.create(owner=self.user, title="Old",
                              amount=5000, date=past_date)
        Expenditure.objects.create(owner=self.user, title="Old Rent",
                                   amount=5000, type="BILL", date=past_date)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["formatted_income"], "£0.00")
        self.assertEqual(response.data["formatted_bills"], "£0.00")

    def test_requires_authentication(self):
        """Should reject unauthenticated requests with 403"""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_entries_outside_date_range_are_excluded(self):
        """Should not count entries just before or after the selected month"""
        # One day before the start of the month
        last_month_end = self.today.replace(day=1) - timedelta(days=1)
        Income.objects.create(
            owner=self.user, title="Old", amount=9999, date=last_month_end)

        # One day after the end of the month
        next_month = self.today.replace(day=28) + timedelta(days=5)
        Income.objects.create(
            owner=self.user, title="Too Late", amount=9999, date=next_month)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["formatted_income"], "£0.00")

    def test_other_users_data_not_included(self):
        """Should exclude financial data from other users"""
        Income.objects.create(
            owner=self.user, title="Mine", amount=10000, date=self.today)
        Income.objects.create(
            owner=self.other_user, title="Theirs",
            amount=99999, date=self.today)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["formatted_income"], "£100.00")

    def test_works_without_budget_entry(self):
        """Should not raise error if no DisposableIncomeBudget exists"""
        Income.objects.create(
            owner=self.user, title="Side Job", amount=20000, date=self.today)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["formatted_budget"], "£0.00")

    def test_disposable_remaining_can_be_negative(self):
        """Should return negative value if user overspends disposable income"""
        DisposableIncomeSpending.objects.create(
            owner=self.user, title="Trip", amount=15000, date=self.today)
        DisposableIncomeBudget.objects.create(
            owner=self.user, amount=10000, date=self.today)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["formatted_remaining_disposable"],
                         "-£50.00")

    def test_partial_data_still_returns_full_structure(self):
        """Should return valid response with only income present"""
        Income.objects.create(owner=self.user, title="Salary",
                              amount=50000, date=self.today)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["formatted_income"], "£500.00")
        self.assertEqual(response.data["formatted_bills"], "£0.00")
        self.assertEqual(
            response.data["formatted_remaining_disposable"], "£0.00")


class WeeklySummaryViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="tester", password="pass")
        self.other_user = User.objects.create_user(
            username="intruder", password="pass")
        self.client.force_authenticate(self.user)
        self.url = "/weekly-summary/"
        self.today = make_aware(datetime.today())

    def test_returns_weekly_data_structure(self):
        """Should return a list of weekly summary dictionaries."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("weeks", response.data)
        self.assertIsInstance(response.data["weeks"], list)
        for week in response.data["weeks"]:
            self.assertIn("week_start", week)
            self.assertIn("week_end", week)
            self.assertIn("income", week)
            self.assertIn("cost", week)
            self.assertIn("summary", week)

    def test_weekly_sums_include_all_sources(self):
        """Should sum income, expenditure, and
        disposable spending into cost."""
        # Week range should include this
        base_date = make_aware(datetime.today().replace(
            day=1, hour=0, minute=0))

        Income.objects.create(
            owner=self.user, title="Job", amount=50000, date=base_date)
        Expenditure.objects.create(
            owner=self.user, title="Rent", amount=20000, date=base_date)
        DisposableIncomeSpending.objects.create(
            owner=self.user, title="Snacks", amount=5000, date=base_date)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        week = response.data["weeks"][0]
        self.assertEqual(week["income"], "£500.00")
        self.assertEqual(week["cost"], "£250.00")
        self.assertEqual(week["summary"], "£250.00")

    def test_excludes_other_users_data(self):
        """Should not include any financial data from another user."""
        base_date = make_aware(datetime.today().replace(
            day=1, hour=0, minute=0))

        Income.objects.create(owner=self.user, title="My Salary",
                              amount=30000, date=base_date)
        Income.objects.create(owner=self.other_user, title="Their Salary",
                              amount=99999, date=base_date)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        week = response.data["weeks"][0]
        self.assertEqual(week["income"], "£300.00")

    def test_requires_authentication(self):
        """Should return 403 if user is not logged in."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_correct_week_boundaries(self):
        """Should show correct ISO format week_start and week_end dates."""
        response = self.client.get(self.url)
        week = response.data["weeks"][0]
        self.assertRegex(week["week_start"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertRegex(week["week_end"], r"^\d{4}-\d{2}-\d{2}$")

    def test_works_with_no_data(self):
        """Should return zeroed-out weekly summaries when no entries exist."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        for week in response.data["weeks"]:
            self.assertEqual(week["income"], "£0.00")
            self.assertEqual(week["cost"], "£0.00")
            self.assertEqual(week["summary"], "£0.00")
