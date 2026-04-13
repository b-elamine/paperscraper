import locale
import random
import re
import time
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://scholar.google.com/scholar"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]


def detect_lang():
    try:
        code = locale.getlocale()[0] or ""
        lang = code.split("_")[0]
        return lang if len(lang) == 2 else "en"
    except Exception:
        return "en"


def build_url(keywords, page, lang, year_low=None, year_high=None):
    params = {
        "q":      keywords,
        "hl":     lang,
        "as_sdt": "0,5",
        "start":  page * 10,
    }
    if year_low:
        params["as_ylo"] = year_low
    if year_high:
        params["as_yhi"] = year_high
    return f"{BASE_URL}?{urlencode(params)}"


def fetch_page(url, session, retries=3, base_wait=10):
    headers = {
        "User-Agent":      random.choice(USER_AGENTS),
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection":      "keep-alive",
        "DNT":             "1",
    }
    for attempt in range(1, retries + 1):
        response = session.get(url, headers=headers, timeout=15)
        if response.status_code == 429:
            if attempt == retries:
                response.raise_for_status()
            wait = base_wait * attempt + random.uniform(0, 5)
            time.sleep(wait)
            continue
        response.raise_for_status()
        return response.text


def parse_page(html):
    soup = BeautifulSoup(html, "html.parser")

    if soup.find("form", {"action": re.compile(r"sorry")}):
        raise RuntimeError("Google returned a CAPTCHA. Wait 20–30 minutes and retry.")

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
                venue_year  = parts[1]
                year_match  = re.search(r"\b(19|20)\d{2}\b", venue_year)
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
                 min_delay=8.0, max_delay=15.0):
    """
    Generator that scrapes one page at a time and yields (page_num, records).
    Delay happens AFTER yielding so the caller can send data before waiting.
    """
    if not lang:
        lang = detect_lang()

    session = requests.Session()

    for page in range(pages):
        url     = build_url(keywords, page, lang, year_low, year_high)
        html    = fetch_page(url, session)
        records = parse_page(html)
        if not records:
            return
        yield page + 1, records
        # Delay after yielding, before next page
        if page < pages - 1:
            time.sleep(random.uniform(min_delay, max_delay))


def run_scrape(keywords, pages, lang=None, year_low=None, year_high=None,
               min_delay=8.0, max_delay=15.0):
    all_results = []
    index       = 1
    for _, records in scrape_pages(keywords, pages, lang, year_low, year_high,
                                   min_delay, max_delay):
        for record in records:
            record["index"] = index
            all_results.append(record)
            index += 1
    return all_results
