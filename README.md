# Credit Card Promotions → Notion (Fully Automated)

Scrape multi-page credit card promo listings (any issuer/bank) and push them into a Notion database.
Automated via GitHub Actions; mobile-friendly via Notion app.

## Notion (one-time)
1) Create a Notion **database** with these properties (names are case-sensitive):
   - **Name** (Title)
   - **Offer** (Rich text)
   - **Category** (Select)
   - **City** (Multi-select)
   - **Issuer** (Select)
   - **Expiry** (Date)
   - **Source URL** (URL)
   - **Last Seen** (Date)
2) Create a Notion **internal integration** and copy the token.
3) Share the database with the integration (**Can edit**).
4) Copy the database URL → get **database_id**.

## Configure pages to scrape
Edit `mapping.py` → fill `PROMO_PAGES` with all section/pagination URLs and the `issuer` name.
Adjust CSS `SELECTORS` if the site’s DOM differs.

## Local run
```bash
python3 -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # fill your secrets
python scraper.py