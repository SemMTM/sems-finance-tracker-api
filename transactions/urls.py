from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ExpenditureViewSet,
)


router = DefaultRouter()
router.register(r'expenditures', ExpenditureViewSet, basename='expenditures')

urlpatterns = [
    path('', include(router.urls)),
]