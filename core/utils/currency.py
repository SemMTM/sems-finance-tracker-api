from transactions.models.currency import Currency

CURRENCY_SYMBOLS = {
    'USD': '$',
    'EUR': '€',
    'JPY': '¥',
    'GBP': '£',
    'AUD': 'A$',
    'CAD': 'C$',
    'CHF': 'CHF',
    'CNY': '¥',
    'HKD': 'HK$',
    'INR': '₹',
}


def get_currency_symbol(code: str) -> str:
    """
    Returns the currency symbol for a given 3-letter currency code.
    Defaults to empty string if not found.
    """
    return CURRENCY_SYMBOLS.get(code.upper(), '')


def get_user_currency_symbol(request, default='GBP'):
    if not request or not request.user.is_authenticated:
        return get_currency_symbol(default)

    user_currency = Currency.objects.filter(owner=request.user).first()
    return get_currency_symbol(
        user_currency.currency if user_currency else default)
