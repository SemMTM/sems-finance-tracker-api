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
