import os
from datetime import datetime, timezone
from notion_client import Client

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

if not NOTION_TOKEN or not NOTION_DATABASE_ID:
    raise RuntimeError("Missing NOTION_TOKEN or NOTION_DATABASE_ID environment variables")

client = Client(auth=NOTION_TOKEN)


def _rich_text(text: str):
    return [{"type": "text", "text": {"content": (text or "")[:1999]}}] if text else []


def _select(name: str | None):
    return {"name": name} if name else None


def _multi(text: str | None):
    if not text:
        return []
    parts = [p.strip() for p in text.split(",") if p.strip()]
    return [{"name": p} for p in parts]


def _today_iso():
    return datetime.now(timezone.utc).date().isoformat()


def _parse_date_fuzzy(s: str) -> str | None:
    """
    Try to parse a date from free text (Arabic/English numerals).
    Returns ISO YYYY-MM-DD or None.
    """
    if not s:
        return None
    import re
    s = s.strip()
    # Normalize Arabic digits to Latin
    arabic_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    s_norm = s.translate(arabic_digits)

    # yyyy-mm-dd or yyyy/mm/dd
    m = re.search(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", s_norm)
    if m:
        y, mo, d = [int(x) for x in m.groups()]
        return f"{y:04d}-{mo:02d}-{d:02d}"

    # dd-mm-yyyy or dd/mm/yyyy
    m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", s_norm)
    if m:
        d, mo, y = [int(x) for x in m.groups()]
        return f"{y:04d}-{mo:02d}-{d:02d}"

    return None


def find_existing_page(name: str, city: str | None, issuer: str | None):
    """
    Query Notion for an existing page:
    - Name (Title) equals
    - City (Multi-select) contains city (if present)
    - Issuer (Select) equals issuer (if present)
    """
    filters = {"and": [{"property": "Name", "title": {"equals": name}}]}

    if city:
        filters["and"].append({"property": "City", "multi_select": {"contains": city}})
    if issuer:
        filters["and"].append({"property": "Issuer", "select": {"equals": issuer}})

    res = client.databases.query(database_id=NOTION_DATABASE_ID, filter=filters)
    results = res.get("results", [])
    return results[0]["id"] if results else None


def upsert_offer(item: dict):
    """
    item keys:
      name, offer, category, city (comma-separated for multi), issuer, expiry (free text or ISO), link
    """
    name = item.get("name")
    offer = item.get("offer")
    category = item.get("category")
    city = item.get("city")
    issuer = item.get("issuer")
    expiry = item.get("expiry")
    link = item.get("link")

    if not name:
        return

    page_id = find_existing_page(name, city, issuer)

    props = {
        "Name": {"title": _rich_text(name)},
        "Offer": {"rich_text": _rich_text(offer)},
        "Category": {"select": _select(category)},
        "City": {"multi_select": _multi(city)},
        "Issuer": {"select": _select(issuer)},
        "Source URL": {"url": link or None},
        "Last Seen": {"date": {"start": _today_iso()}},
    }

    # Expiry as date if we can parse it
    if expiry:
        iso = _parse_date_fuzzy(expiry)
        if iso:
            props["Expiry"] = {"date": {"start": iso}}

    if page_id:
        client.pages.update(page_id=page_id, properties=props)
    else:
        client.pages.create(parent={"database_id": NOTION_DATABASE_ID}, properties=props)