from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from transactions.models import (
    Income,
    Expenditure,
    DisposableIncomeBudget,
    DisposableIncomeSpending
)

class Command(BaseCommand):
    help = 'Delete all financial data for user "sem" to reset their account.'

    def handle(self, *args, **options):
        User = get_user_model()
        try:
            user = User.objects.get(username='sem')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('User "sem" not found.'))
            return

        # Delete all related data
        Income.objects.filter(owner=user).delete()
        Expenditure.objects.filter(owner=user).delete()
        DisposableIncomeBudget.objects.filter(owner=user).delete()
        DisposableIncomeSpending.objects.filter(owner=user).delete()

        self.stdout.write(self.style.SUCCESS('All data for user "sem" has been deleted.'))