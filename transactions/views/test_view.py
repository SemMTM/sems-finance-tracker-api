from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


class TestHomepageDataView(APIView):
    """
    A public view that returns mock homepage data for PageSpeed testing.
    No auth required.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        # Use mock data or safe test data
        return Response({
            "monthly_summary": {
                "income": 500000,
                "expenditure": 320000,
                "currency": "£"
            },
            "recent_transactions": [
                {"title": "Rent", "amount": 100000, "date": "2025-05-01"},
                {"title": "Groceries", "amount": 4000, "date": "2025-05-02"},
                {"title": "Salary", "amount": 500000, "date": "2025-05-01"},
            ]
        })
