"""
Google Scholar scraper using Playwright (headless Chrome).

Same interface as scraper.py so it can be dropped in as a replacement:
  - scrape_pages(keywords, pages, lang, year_low, year_high) -> generator of (page_num, records)
  - run_scrape(keywords, pages, lang, year_low, year_high)   -> list of records

To install:
  pip install playwright
  playwright install chromium

To plug into the web app later, in app.py replace:
  from scraper import scrape_pages as scholar_scrape_pages
with:
  from playwright_scraper import scrape_pages as scholar_scrape_pages

To plug into the CLI later, in web-scraper.py add "scholar-pw" as a source option
and import run_scrape from here.
"""

import locale
import random
import re
import time
from urllib.parse import urlencode

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


BASE_URL = "https://scholar.google.com/scholar"


def detect_lang():
    try:
        code = locale.getlocale()[0] or ""
        lang = code.split("_")[0]
        return lang if len(lang) == 2 else "en"
    except Exception:
        return "en"


def _build_url(keywords, page, lang="en", year_low=None, year_high=None):
    params = {
        "q":      keywords,
        "hl":     lang or "en",
        "as_sdt": "0,5",
        "start":  page * 10,
    }
    if year_low:
        params["as_ylo"] = year_low
    if year_high:
        params["as_yhi"] = year_high
    return f"{BASE_URL}?{urlencode(params)}"


def _parse_page(html):
    soup = BeautifulSoup(html, "html.parser")

    if soup.find("form", {"action": re.compile(r"sorry")}):
        raise RuntimeError(
            "Google returned a CAPTCHA page. wait 30 min and try again."
        )

    results = []
    for item in soup.select("div.gs_r.gs_or.gs_scl"):
        title_tag = item.select_one("h3.gs_rt a")
        if title_tag:
            title = title_tag.get_text(strip=True)
            url   = title_tag.get("href", "N/A")
        else:
            title_tag = item.select_one("h3.gs_rt")
            title = title_tag.get_text(strip=True) if title_tag else "N/A"
            url   = "N/A"

        meta_tag = item.select_one("div.gs_a")
        authors, venue, year = "N/A", "N/A", "N/A"
        if meta_tag:
            meta  = meta_tag.get_text(separator=" ", strip=True)
            parts = [p.strip() for p in meta.split(" - ")]
            if parts:
                authors = parts[0]
            if len(parts) >= 2:
                venue_year = parts[1]
                year_match = re.search(r"\b(19|20)\d{2}\b", venue_year)
                if year_match:
                    year  = year_match.group(0)
                    venue = venue_year.replace(year, "").strip(" ,")
                else:
                    venue = venue_year

        abstract_tag = item.select_one("div.gs_rs")
        abstract = abstract_tag.get_text(strip=True) if abstract_tag else ""

        results.append({
            "title":    title,
            "authors":  authors,
            "year":     year,
            "venue":    venue,
            "url":      url,
            "abstract": abstract[:300],
        })

    return results


def scrape_pages(keywords, pages, lang=None, year_low=None, year_high=None,
                 min_delay=3.0, max_delay=6.0):
    """
    Generator that yields (page_num, records) one page at a time.
    Uses a real headless Chrome browser so Google sees it as a normal user.
    Delays are short (3-6s) because a real browser is much less suspicious.
    """
    lang = lang or detect_lang()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale=f"{lang}-{lang.upper()}",
        )
        page = context.new_page()

        try:
            for page_num in range(pages):
                url = _build_url(keywords, page_num, lang, year_low, year_high)

                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=20000)
                    page.wait_for_selector(
                        "div.gs_r, form[action*='sorry']",
                        timeout=10000,
                    )
                except PlaywrightTimeout:
                    raise RuntimeError(
                        "Google Scholar timed out. check your connection."
                    )

                records = _parse_page(page.content())

                if not records:
                    break

                yield page_num + 1, records

                if page_num < pages - 1:
                    time.sleep(random.uniform(min_delay, max_delay))

        finally:
            browser.close()


def run_scrape(keywords, pages, lang=None, year_low=None, year_high=None,
               min_delay=3.0, max_delay=6.0):
    all_results = []
    index       = 1
    for _, records in scrape_pages(keywords, pages, lang, year_low, year_high,
                                   min_delay, max_delay):
        for record in records:
            record["index"] = index
            all_results.append(record)
            index += 1
    return all_results
