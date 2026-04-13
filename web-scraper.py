"""
Google Scholar Scraper
======================
Scrapes paper titles, authors, publication year, and URL from Google Scholar
by directly requesting the same URLs your browser uses.

Usage:
    python web-scraper.py -k "machine learning" -p 5
    python web-scraper.py -k "sobriété informatique" -p 10 --year-low 2020 --year-high 2024
    python web-scraper.py -k "deep learning" -p 20 -o results.csv

Arguments:
    -k / --keywords   Search query (required)
    -p / --pages      Number of Scholar pages to scrape (default: 10, max: 100)
    --year-low        Filter: earliest publication year  (optional)
    --year-high       Filter: latest  publication year  (optional)
    -o / --output     Output CSV filename (default: scholar_results.csv)
    --min-delay       Min seconds between pages (default: 3)
    --max-delay       Max seconds between pages (default: 6)

Tips to avoid blocks:
    - Keep delays at defaults (3-6 s per page).
    - If you hit a CAPTCHA, wait 20-30 min then retry.
"""

import argparse
import csv
import time
import random
import sys
import re
from datetime import datetime
from urllib.parse import urlencode

import locale
import requests
from bs4 import BeautifulSoup


BASE_URL = "https://scholar.google.com/scholar"


def detect_lang():
    """Return the 2-letter language code from the system locale (e.g. 'fr', 'en')."""
    try:
        code = locale.getlocale()[0] or ""   # e.g. 'fr_FR'
        lang = code.split("_")[0]
        return lang if len(lang) == 2 else "en"
    except Exception:
        return "en"

# Rotate through several realistic browser User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]


# ─────────────────────────────────────────────────────────────────────────────


def parse_args():
    parser = argparse.ArgumentParser(
        description="Scrape Google Scholar papers by keyword.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "-k", "--keywords",
        required=True,
        help="Search query / keywords (e.g. 'machine learning')",
    )
    parser.add_argument(
        "-p", "--pages",
        type=int,
        default=10,
        metavar="N",
        help="Number of Scholar pages to scrape (10 results/page, default: 10)",
    )
    parser.add_argument(
        "--year-low",
        type=int,
        default=None,
        dest="year_low",
        help="Filter results from this year onward (optional)",
    )
    parser.add_argument(
        "--year-high",
        type=int,
        default=None,
        dest="year_high",
        help="Filter results up to this year (optional)",
    )
    parser.add_argument(
        "-o", "--output",
        default="scholar_results.csv",
        help="Output CSV filename (default: scholar_results.csv)",
    )
    parser.add_argument(
        "--lang",
        default=None,
        help="Language code for Scholar (e.g. 'fr', 'en'). Auto-detected from system if not set.",
    )
    parser.add_argument(
        "--min-delay",
        type=float,
        default=3.0,
        dest="min_delay",
        help="Min seconds to wait between pages (default: 3)",
    )
    parser.add_argument(
        "--max-delay",
        type=float,
        default=6.0,
        dest="max_delay",
        help="Max seconds to wait between pages (default: 6)",
    )
    return parser.parse_args()


# ─────────────────────────────────────────────────────────────────────────────


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


def fetch_page(url, session):
    headers = {
        "User-Agent":      random.choice(USER_AGENTS),
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection":      "keep-alive",
        "DNT":             "1",
    }
    response = session.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.text


def parse_page(html):
    soup = BeautifulSoup(html, "html.parser")

    # Detect CAPTCHA
    if soup.find("form", {"action": re.compile(r"sorry")}):
        raise RuntimeError(
            "Google returned a CAPTCHA page. "
            "Wait 20-30 minutes and retry, or use a VPN."
        )

    results = []
    for item in soup.select("div.gs_r.gs_or.gs_scl"):
        # Title and link
        title_tag = item.select_one("h3.gs_rt a")
        if title_tag:
            title = title_tag.get_text(strip=True)
            url   = title_tag.get("href", "N/A")
        else:
            # Sometimes the title has no link (book, citation-only)
            title_tag = item.select_one("h3.gs_rt")
            title = title_tag.get_text(strip=True) if title_tag else "N/A"
            url   = "N/A"

        # Authors, venue, year — all packed in one line like:
        # "A Author, B Author - Journal Name, 2022 - publisher.com"
        meta_tag = item.select_one("div.gs_a")
        authors, venue, year = "N/A", "N/A", "N/A"
        if meta_tag:
            meta = meta_tag.get_text(separator=" ", strip=True)
            parts = [p.strip() for p in meta.split(" - ")]
            if parts:
                authors = parts[0]
            if len(parts) >= 2:
                # Second segment is "Venue, Year" or just "Year"
                venue_year = parts[1]
                year_match = re.search(r"\b(19|20)\d{2}\b", venue_year)
                if year_match:
                    year = year_match.group(0)
                    venue = venue_year.replace(year, "").strip(" ,")
                else:
                    venue = venue_year

        # Abstract snippet
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


# ─────────────────────────────────────────────────────────────────────────────


def scrape(args):
    year_info = ""
    if args.year_low or args.year_high:
        year_info = f" | years: {args.year_low or '?'} – {args.year_high or '?'}"

    lang = args.lang if args.lang else detect_lang()

    print(f"\nSearching Google Scholar for: '{args.keywords}'{year_info}")
    print(f"Locale: {lang} | Target: {args.pages} page(s) (~{args.pages * 10} results)\n")

    session = requests.Session()
    all_results = []
    index = 1

    for page in range(args.pages):
        url = build_url(args.keywords, page, lang, args.year_low, args.year_high)
        print(f"  [page {page + 1}/{args.pages}] {url}")

        html    = fetch_page(url, session)
        records = parse_page(html)

        if not records:
            print("  [!] No results found on this page — stopping early.")
            break

        for record in records:
            record["index"] = index
            all_results.append(record)
            print(f"    [{index:>3}] {record['title'][:75]}")
            index += 1

        if page < args.pages - 1:
            delay = random.uniform(args.min_delay, args.max_delay)
            print(f"\n  --- waiting {delay:.1f}s before next page ---\n")
            time.sleep(delay)

    return all_results


# ─────────────────────────────────────────────────────────────────────────────


def save_csv(records, output_path):
    if not records:
        print("\n[!] No results to save.")
        return

    fieldnames = ["index", "title", "authors", "year", "venue", "url", "abstract"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"\n✓ Saved {len(records)} record(s) → {output_path}")


# ─────────────────────────────────────────────────────────────────────────────


def main():
    args = parse_args()

    if args.pages < 1 or args.pages > 100:
        sys.exit("[ERROR] --pages must be between 1 and 100.")
    if args.min_delay > args.max_delay:
        sys.exit("[ERROR] --min-delay cannot be greater than --max-delay.")

    start = datetime.now()
    print("=" * 65)
    print("  Google Scholar Scraper")
    print(f"  Started : {start.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    try:
        records = scrape(args)
        save_csv(records, args.output)
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user.")
        sys.exit(0)
    except RuntimeError as e:
        print(f"\n[BLOCKED] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        raise

    elapsed = (datetime.now() - start).seconds
    print(f"  Duration : {elapsed}s")
    print("=" * 65)


if __name__ == "__main__":
    main()
