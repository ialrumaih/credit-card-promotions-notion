# Configure the pages you want to scrape and how to read them.

PROMO_PAGES = [
    # SAB – dynamic page (JS-rendered)
    {
        "url": "https://www.sab.com/ar/personal/compare-credit-cards/credit-card-special-offers/all-offers/",
        "issuer": "SAB",
        "default_category": None,
        "requires_js": True,  # use Playwright
    },

    # Example: NCB/AlAhli (replace/extend as needed; set requires_js based on actual rendering)
    {
        "url": "https://www.alahli.com/ar/pages/personal-banking/credit-cards/credit-card-promotions/views",
        "issuer": "NCB",
        "default_category": None,
        "requires_js": True,  # set to False if static HTML is enough
    },

    # Add more pages (and issuers) below as needed...
]

# CSS selectors tuned to be resilient across different issuers.
# We use broad "contains" class-name matching to handle layout variance.
SELECTORS = {
    # any “offer/promo/card/tile/list item” container
    "card": (
        "[class*='offer'], [class*='promo'], [class*='card'], "
        "[class*='tile'], article, li"
    ),

    # title/name/heading likely inside headings or title-like classes
    "name": "h1, h2, h3, h4, [class*='title'], [class*='name'], [class*='heading']",

    # main description/body text
    "offer": "[class*='desc'], [class*='body'], [class*='copy'], p",

    # category chip/label if present
    "category": "[class*='category'], [data-category]",

    # city/location text or chip
    "city": "[class*='city'], [class*='location'], [data-city]",

    # expiry/date; time tags or elements with “date/expiry”
    "expiry": "time[datetime], time, [class*='date'], [class*='expiry']",

    # link from within a card
    "link": "a[href]",
}

# Heuristic mapping from Arabic keywords to normalized Category labels
CATEGORY_MAP = {
    "مطاعم": "Dining",
    "مطعم": "Dining",
    "تسوق": "Shopping",
    "سفر": "Travel",
    "فنادق": "Hotels",
    "الكترونيات": "Electronics",
}

# Normalize common Arabic city names to consistent English tags
CITY_NORMALIZATION = {
    "الرياض": "Riyadh",
    "جدة": "Jeddah",
    "مكة": "Makkah",
    "الخبر": "Khobar",
    "الدمام": "Dammam",
    "المدينة": "Madinah",
}