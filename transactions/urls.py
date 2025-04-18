from django.urls import path, include
from rest_framework.routers import DefaultRouter
from transactions.views.monthly_summary import MonthlySummaryView
from .views import (
    ExpenditureViewSet,
    IncomeViewSet,
    DisposableIncomeSpendingViewSet,
    DisposableIncomeBudgetViewSet,
    CurrencyViewSet,
)


router = DefaultRouter()
router.register(r'expenditures', ExpenditureViewSet, basename='expenditures')
router.register(r'income', IncomeViewSet, basename='income')
router.register(r'disposable-spending', DisposableIncomeSpendingViewSet,
                basename='disposable-spending')
router.register(r'disposable-budget', DisposableIncomeBudgetViewSet,
                basename='disposable-budget')
router.register(r'currency', CurrencyViewSet, basename='currency')

urlpatterns = [
    path('', include(router.urls)),
    path('monthly-summary/', MonthlySummaryView.as_view(),
         name='monthly-summary'),
]
