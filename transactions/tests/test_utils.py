from django.test import TestCase
from django.contrib.auth.models import User
from django.utils.timezone import make_aware, now
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from calendar import monthrange
from transactions.models import (
    Income,
    Expenditure,
    DisposableIncomeSpending,
    DisposableIncomeBudget,
)
from transactions.utils import (
    generate_weekly_repeats_for_6_months,
    generate_monthly_repeats_for_6_months,
    generate_6th_month_repeats,
    clean_old_transactions
  )
import uuid


class GenerateWeeklyRepeatsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='tester', password='pass')
        self.base_date = make_aware(datetime(2025, 1, 15))
        self.entry = Income.objects.create(
            owner=self.user,
            title="Weekly Pay",
            amount=10000,
            repeated="WEEKLY",
            date=self.base_date,
            repeat_group_id=None
        )

    def test_generates_repeats_up_to_end_of_6th_month(self):
        """Should generate entries weekly until
        the last day of the 6th month."""
        generate_weekly_repeats_for_6_months(self.entry, Income)

        # Count how many repeats were generated (excluding the original)
        repeats = Income.objects.filter(
            repeat_group_id=self.entry.repeat_group_id
        ).exclude(pk=self.entry.pk)

        self.assertTrue(repeats.exists())
        last_repeat = repeats.order_by('date').last()

        expected_final_date = self.base_date.replace(
            day=1) + relativedelta(months=5)
        expected_final_date = expected_final_date.replace(
            day=(expected_final_date + relativedelta(
                months=1) - timedelta(days=1)).day
        )

        self.assertLessEqual(
            last_repeat.date.date(), expected_final_date.date())

    def test_assigns_repeat_group_id_if_none_exists(self):
        """Should assign a new UUID repeat_group_id to the
        base entry if missing."""
        self.assertIsNone(self.entry.repeat_group_id)
        generate_weekly_repeats_for_6_months(self.entry, Income)
        self.entry.refresh_from_db()
        self.assertIsInstance(self.entry.repeat_group_id, uuid.UUID)

    def test_repeat_entries_replicate_base_fields(self):
        """Repeat entries should copy title, amount, and repeated fields."""
        generate_weekly_repeats_for_6_months(self.entry, Income)
        repeats = Income.objects.filter(
            repeat_group_id=self.entry.repeat_group_id
        ).exclude(pk=self.entry.pk)

        for r in repeats:
            self.assertEqual(r.title, self.entry.title)
            self.assertEqual(r.amount, self.entry.amount)
            self.assertEqual(r.repeated, self.entry.repeated)
            self.assertEqual(r.owner, self.entry.owner)

    def test_does_not_create_if_already_has_group_id(self):
        """Should not overwrite an existing repeat_group_id on re-call."""
        original_group_id = uuid.uuid4()
        self.entry.repeat_group_id = original_group_id
        self.entry.save(update_fields=["repeat_group_id"])

        generate_weekly_repeats_for_6_months(self.entry, Income)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.repeat_group_id, original_group_id)

    def test_handles_end_of_month_start_dates_gracefully(self):
        """Should correctly generate dates even when base
        date is at end of month."""
        self.entry.date = make_aware(datetime(2025, 1, 31))  # January 31st
        self.entry.save()

        generate_weekly_repeats_for_6_months(self.entry, Income)
        repeats = Income.objects.filter(
            repeat_group_id=self.entry.repeat_group_id)

        # Should not error out or create invalid dates
        self.assertTrue(all(r.date.day <= 31 for r in repeats))

    def test_creates_expected_number_of_weekly_repeats(self):
        """Should create approximately 26 weekly repeats within 6 months."""
        generate_weekly_repeats_for_6_months(self.entry, Income)
        repeat_count = Income.objects.filter(
            repeat_group_id=self.entry.repeat_group_id).exclude(
                pk=self.entry.pk).count()

        # Between 21 and 27 weeks depending on month length
        self.assertTrue(21 <= repeat_count <= 27)

    def test_preserves_existing_repeat_group_id(self):
        """Should not override a manually assigned repeat_group_id."""
        manual_id = uuid.uuid4()
        self.entry.repeat_group_id = manual_id
        self.entry.save()

        generate_weekly_repeats_for_6_months(self.entry, Income)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.repeat_group_id, manual_id)


class GenerateMonthlyRepeatsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="tester", password="pass")
        self.base_date = make_aware(datetime(2025, 1, 31))
        self.entry = Income.objects.create(
            owner=self.user,
            title="Monthly Salary",
            amount=10000,
            repeated="MONTHLY",
            date=self.base_date,
            repeat_group_id=None,
        )

    def test_creates_repeats_for_next_5_months(self):
        """Should create 5 monthly repeat entries from the base date."""
        generate_monthly_repeats_for_6_months(self.entry, Income)
        repeats = Income.objects.filter(
            repeat_group_id=self.entry.repeat_group_id).exclude(
                pk=self.entry.pk)
        self.assertEqual(repeats.count(), 5)

    def test_repeat_group_id_is_created_if_missing(self):
        """Should assign a repeat_group_id to base entry if missing."""
        self.assertIsNone(self.entry.repeat_group_id)
        generate_monthly_repeats_for_6_months(self.entry, Income)
        self.entry.refresh_from_db()
        self.assertIsInstance(self.entry.repeat_group_id, uuid.UUID)

    def test_copies_relevant_fields_from_base(self):
        """Each repeated entry should copy key fields from base entry."""
        generate_monthly_repeats_for_6_months(self.entry, Income)
        for repeat in Income.objects.filter(
            repeat_group_id=self.entry.repeat_group_id).exclude(
                pk=self.entry.pk):
            self.assertEqual(repeat.title, self.entry.title)
            self.assertEqual(repeat.amount, self.entry.amount)
            self.assertEqual(repeat.repeated, self.entry.repeated)
            self.assertEqual(repeat.owner, self.entry.owner)

    def test_preserves_existing_repeat_group_id(self):
        """Should not overwrite manually set repeat_group_id."""
        manual_id = uuid.uuid4()
        self.entry.repeat_group_id = manual_id
        self.entry.save(update_fields=["repeat_group_id"])
        generate_monthly_repeats_for_6_months(self.entry, Income)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.repeat_group_id, manual_id)

    def test_rollover_behavior_preserves_monthly_semantics(self):
        """
        Should roll forward to valid last day if base day
        doesn't exist in target month,
        and resume original day when possible.
        """
        self.entry.date = make_aware(datetime(2025, 1, 31))  # Jan 31
        self.entry.save()

        generate_monthly_repeats_for_6_months(self.entry, Income)

        repeats = Income.objects.filter(
            repeat_group_id=self.entry.repeat_group_id
        ).exclude(pk=self.entry.pk).order_by('date')

        dates = [r.date.date() for r in repeats]
        expected = [
            datetime(2025, 2, 28).date(),
            # Feb adjusts to 28 (2025 is not leap year)
            datetime(2025, 3, 31).date(),  # March supports 31
            datetime(2025, 4, 30).date(),  # April max is 30
            datetime(2025, 5, 31).date(),
            datetime(2025, 6, 30).date(),
        ]

        self.assertEqual(dates, expected)


class Generate6thMonthRepeatsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="tester", password="pass")
        self.current_month = datetime(2025, 1, 1)
        self.fifth_month = make_aware(
            self.current_month + relativedelta(months=4))
        self.sixth_month = make_aware(
            self.current_month + relativedelta(months=5))

    def test_creates_monthly_repeat_in_6th_month(self):
        """Should clone monthly entry from 5th month into 6th month."""
        entry = Income.objects.create(
            owner=self.user,
            title="Monthly Bonus",
            amount=5000,
            date=self.fifth_month.replace(day=15),
            repeated="MONTHLY",
            repeat_group_id=uuid.uuid4()
        )

        generate_6th_month_repeats(Income, self.user, self.current_month)
        new_date = entry.date + relativedelta(months=1)

        self.assertTrue(Income.objects.filter(date=new_date).exists())

    def test_creates_weekly_repeats_from_last_fifth_month_entry(self):
        """Should continue weekly repeats into the 6th month."""
        base_date = self.fifth_month.replace(day=1)
        group_id = uuid.uuid4()
        Income.objects.create(
            owner=self.user,
            title="Weekly Pay",
            amount=1000,
            date=base_date,
            repeated="WEEKLY",
            repeat_group_id=group_id
        )
        Income.objects.create(
            owner=self.user,
            title="Weekly Pay",
            amount=1000,
            date=base_date + timedelta(days=7),
            repeated="WEEKLY",
            repeat_group_id=group_id
        )

        generate_6th_month_repeats(Income, self.user, self.current_month)

        entries = Income.objects.filter(
            repeat_group_id=group_id,
            date__gte=self.sixth_month.replace(day=1)
        )
        self.assertTrue(entries.exists())

    def test_skips_duplicate_if_already_exists(self):
        """Should not create duplicates if repeat for same date already
        exists."""
        group_id = uuid.uuid4()
        base = Income.objects.create(
            owner=self.user,
            title="Monthly",
            amount=9999,
            date=self.fifth_month.replace(day=20),
            repeated="MONTHLY",
            repeat_group_id=group_id
        )
        # Already created manually
        Income.objects.create(
            owner=self.user,
            title="Monthly",
            amount=9999,
            date=base.date + relativedelta(months=1),
            repeated="MONTHLY",
            repeat_group_id=group_id
        )

        generate_6th_month_repeats(Income, self.user, self.current_month)

        count = Income.objects.filter(
            repeat_group_id=group_id,
            date__month=(self.fifth_month.month + 1) % 12
        ).count()
        self.assertEqual(count, 1)

    def test_handles_end_of_month_rollover(self):
        """Should handle February from January 31st correctly."""
        jan_31 = self.fifth_month.replace(day=31)
        entry = Income.objects.create(
            owner=self.user,
            title="Edge Date",
            amount=2000,
            date=jan_31,
            repeated="MONTHLY",
            repeat_group_id=uuid.uuid4()
        )
        generate_6th_month_repeats(Income, self.user, self.current_month)

        expected_date = entry.date + relativedelta(months=1)
        max_day = monthrange(expected_date.year, expected_date.month)[1]
        adjusted = expected_date.replace(day=min(entry.date.day, max_day))

        self.assertTrue(Income.objects.filter(date=adjusted).exists())

    def test_weekly_entry_without_group_id_is_skipped(self):
        """Should skip weekly repeat entries that lack a repeat_group_id."""
        Income.objects.create(
            owner=self.user,
            title="No Group Weekly",
            amount=1000,
            date=self.fifth_month.replace(day=5),
            repeated="WEEKLY",
            repeat_group_id=None  # no group ID
        )
        generate_6th_month_repeats(Income, self.user, self.current_month)
        entries = Income.objects.filter(date__gte=self.sixth_month)
        self.assertEqual(entries.count(), 0)

    def test_does_not_generate_repeats_for_other_users(self):
        """Should not generate any entries for
        users other than the one specified."""
        other_user = User.objects.create_user(
            username="other", password="pass")
        Income.objects.create(
            owner=other_user,
            title="Their Income",
            amount=8888,
            date=self.fifth_month.replace(day=10),
            repeated="MONTHLY",
            repeat_group_id=uuid.uuid4()
        )
        generate_6th_month_repeats(Income, self.user, self.current_month)
        self.assertFalse(Income.objects.filter(owner=self.user).exists())

    def test_cloned_entries_share_repeat_group_id(self):
        """Should ensure all repeated entries inherit the
        original repeat_group_id."""
        base = Income.objects.create(
            owner=self.user,
            title="Linked Entry",
            amount=1000,
            date=self.fifth_month.replace(day=15),
            repeated="MONTHLY",
            repeat_group_id=uuid.uuid4()
        )
        generate_6th_month_repeats(Income, self.user, self.current_month)
        repeats = Income.objects.filter(
            repeat_group_id=base.repeat_group_id,
            date__gt=base.date
        )
        self.assertTrue(repeats.exists())

    def test_no_data_in_fifth_month_creates_nothing(self):
        """Should create no entries if the user has
        no eligible data in the 5th month."""
        generate_6th_month_repeats(Income, self.user, self.current_month)
        self.assertEqual(Income.objects.count(), 0)

    def test_cloned_entry_fields_match_base(self):
        """Should ensure repeated entries copy all
        relevant fields from the base entry."""
        base = Income.objects.create(
            owner=self.user,
            title="Original",
            amount=12000,
            repeated="MONTHLY",
            date=self.fifth_month.replace(day=18),
            repeat_group_id=uuid.uuid4()
        )
        generate_6th_month_repeats(Income, self.user, self.current_month)
        clone = Income.objects.get(
            date=base.date + relativedelta(months=1))
        self.assertEqual(clone.title, base.title)
        self.assertEqual(clone.amount, base.amount)
        self.assertEqual(clone.repeated, base.repeated)


class CleanOldTransactionsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="tester", password="pass")
        self.other_user = User.objects.create_user(
            username="other", password="pass")
        self.today = now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.cutoff = self.today.replace(day=1) - relativedelta(months=6)
        self.models = [
            Income,
            Expenditure,
            DisposableIncomeSpending,
            DisposableIncomeBudget
          ]

    def _create_entry(self, model, owner, date):
        """Helper to create entries for each model."""
        kwargs = {
            "owner": owner,
            "amount": 1000,
            "date": make_aware(datetime.combine(date, datetime.min.time())),
        }

        if model in [Income, Expenditure]:
            kwargs["title"] = "Test"
        if model == Expenditure:
            kwargs["type"] = "BILL"
        if model == Income or model == Expenditure:
            kwargs["repeated"] = "NEVER"
        if model == DisposableIncomeBudget:
            kwargs.pop("title", None)  # no title field

        return model.objects.create(**kwargs)

    def test_deletes_old_entries_for_all_models(self):
        """Should delete all entries older than cutoff across all models."""
        for model in self.models:
            self._create_entry(
                model, self.user, self.cutoff - timedelta(days=1))

        clean_old_transactions(self.user)

        for model in self.models:
            self.assertEqual(model.objects.filter(owner=self.user).count(), 0)

    def test_keeps_recent_entries(self):
        """Should retain entries from within the visible 6-month window."""
        for model in self.models:
            self._create_entry(
                model, self.user, self.cutoff + timedelta(days=1))

        clean_old_transactions(self.user)

        for model in self.models:
            self.assertEqual(model.objects.filter(owner=self.user).count(), 1)

    def test_does_not_delete_other_users_data(self):
        """Should not affect financial data from other users."""
        for model in self.models:
            self._create_entry(
                model, self.other_user, self.cutoff - timedelta(days=1))

        clean_old_transactions(self.user)

        for model in self.models:
            self.assertEqual(
                model.objects.filter(owner=self.other_user).count(), 1)

    def test_mixed_old_and_new_entries(self):
        """Should delete only old entries and retain recent ones."""
        for model in self.models:
            self._create_entry(
                model, self.user, self.cutoff - timedelta(days=1))
            self._create_entry(
                model, self.user, self.cutoff + timedelta(days=1))

        clean_old_transactions(self.user)

        for model in self.models:
            entries = model.objects.filter(owner=self.user)
            self.assertEqual(entries.count(), 1)
            self.assertTrue(entries.first().date >= self.cutoff)
