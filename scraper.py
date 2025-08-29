import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dotenv import load_dotenv

from mapping import PROMO_PAGES, SELECTORS, CATEGORY_MAP, CITY_NORMALIZATION
from notion_api import upsert_offer

load_dotenv()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "ar,ar-SA;q=0.9,en;q=0.8",
}


def fetch(url: str) -> str:
    """Fetch static HTML via requests."""
    r = requests.get(url, headers=HEADERS, timeout=45)
    r.raise_for_status()
    return r.text


# Playwright path for JS-rendered pages (enabled automatically per page config)
from playwright.sync_api import sync_playwright  # noqa: E402


def fetch_with_js(url: str) -> str:
    """Render page with a headless browser and return full HTML."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        html = page.content()
        browser.close()
        return html


def text_of(node, selector: str) -> str:
    if not selector:
        return ""
    el = node.select_one(selector)
    if not el:
        return ""
    return el.get_text(" ", strip=True)


def clean_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def normalize_category(s: str, default: str | None = None) -> str | None:
    s_norm = clean_whitespace(s).lower()
    for k, v in CATEGORY_MAP.items():
        if k in s_norm:
            return v
    if default:
        return default
    return s_norm.title() if s_norm else None


def normalize_city(s: str) -> str:
    s_norm = clean_whitespace(s)
    return CITY_NORMALIZATION.get(s_norm, s_norm)


def extract_cards(html: str, base_url: str, default_category: str | None = None) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(SELECTORS["card"]) or []
    items: list[dict] = []

    for c in cards:
        name = clean_whitespace(text_of(c, SELECTORS["name"]))
        offer = clean_whitespace(text_of(c, SELECTORS["offer"]))
        category_raw = clean_whitespace(text_of(c, SELECTORS["category"]))
        city_raw = clean_whitespace(text_of(c, SELECTORS["city"]))
        expiry = clean_whitespace(text_of(c, SELECTORS["expiry"]))
        link_el = c.select_one(SELECTORS["link"]) if SELECTORS.get("link") else None
        link = urljoin(base_url, link_el.get("href")) if link_el and link_el.get("href") else base_url

        category = normalize_category(category_raw, default=default_category)
        city = normalize_city(city_raw)

        # Basic validity: must have a name and some offer text
        if name and offer:
            items.append(
                {
                    "name": name,
                    "offer": offer,
                    "category": category,
                    "city": city,
                    "expiry": expiry,
                    "link": link,
                }
            )

    return items


def run():
    all_items: list[dict] = []

    for cfg in PROMO_PAGES:
        url = cfg["url"]
        issuer = cfg.get("issuer")
        default_category = cfg.get("default_category")
        requires_js = cfg.get("requires_js", False)

        try:
            html = fetch_with_js(url) if requires_js else fetch(url)
            items = extract_cards(html, url, default_category=default_category)
            for it in items:
                it["issuer"] = issuer
            all_items.extend(items)
            time.sleep(1)
        except Exception as e:
            print(f"[WARN] Failed {url}: {e}")

    # Deduplicate by (name, city, issuer)
    dedup: dict[tuple[str, str, str], dict] = {}
    for it in all_items:
        key = (it.get("name") or "", it.get("city") or "", it.get("issuer") or "")
        prev = dedup.get(key)
        if not prev:
            dedup[key] = it
            continue

        # Prefer item with expiry, else longer offer text
        prev_exp, curr_exp = bool(prev.get("expiry")), bool(it.get("expiry"))
        if curr_exp and not prev_exp:
            dedup[key] = it
        elif curr_exp == prev_exp and len((it.get("offer") or "")) > len((prev.get("offer") or "")):
            dedup[key] = it

    # Upsert into Notion
    for it in dedup.values():
        upsert_offer(it)

    print(f"Done. Synced {len(dedup)} offers to Notion.")


if __name__ == "__main__":
    run()