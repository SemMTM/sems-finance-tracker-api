from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ExpenditureViewSet,
    IncomeViewSet,
)


router = DefaultRouter()
router.register(r'expenditures', ExpenditureViewSet, basename='expenditures')
router.register(r'income', IncomeViewSet, basename='income')

urlpatterns = [
    path('', include(router.urls)),
]
