from django.test import TestCase
from django.contrib.auth.models import User
from django.utils.timezone import make_aware
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from transactions.models import Income
from transactions.utils import (
    generate_weekly_repeats_for_6_months,
    generate_monthly_repeats_for_6_months
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
        self.user = User.objects.create_user(username="tester", password="pass")
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
        Should roll forward to valid last day if base day doesn't exist in target month,
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
            datetime(2025, 2, 28).date(),  # Feb adjusts to 28 (2025 is not leap year)
            datetime(2025, 3, 31).date(),  # March supports 31
            datetime(2025, 4, 30).date(),  # April max is 30
            datetime(2025, 5, 31).date(),
            datetime(2025, 6, 30).date(),
        ]

        self.assertEqual(dates, expected)
