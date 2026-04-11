"""
Google Scholar Scraper
======================
Scrapes paper titles, authors, publication year, and URL from Google Scholar.

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
    --min-delay       Min seconds between requests (default: 8)
    --max-delay       Max seconds between requests (default: 15)
    --tor             Enable Tor proxy (requires Tor running on port 9050)

Tips to avoid blocks:
    - Keep delays generous (default 8-15 s).
    - If you hit a CAPTCHA, wait ~30 min then retry.
    - Use --tor for better anonymity (requires Tor installed).
"""

import argparse
import csv
import time
import random
import sys
from datetime import datetime


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
        "--min-delay",
        type=float,
        default=8.0,
        dest="min_delay",
        help="Min seconds between requests (default: 8)",
    )
    parser.add_argument(
        "--max-delay",
        type=float,
        default=15.0,
        dest="max_delay",
        help="Max seconds between requests (default: 15)",
    )
    parser.add_argument(
        "--tor",
        action="store_true",
        help="Use Tor proxy for anonymity (requires Tor running on port 9050)",
    )
    return parser.parse_args()


# ─────────────────────────────────────────────────────────────────────────────


def setup_tor():
    try:
        from scholarly import ProxyGenerator, scholarly as _scholarly
        pg = ProxyGenerator()
        success = pg.Tor_Internal(tor_cmd="tor")
        if success:
            _scholarly.use_proxy(pg)
            print("[+] Tor proxy active.")
        else:
            print("[!] Could not start Tor — running without proxy.")
    except Exception as e:
        print(f"[!] Tor setup failed: {e}")


def scrape(args):
    try:
        from scholarly import scholarly
    except ImportError:
        sys.exit(
            "\n[ERROR] 'scholarly' is not installed.\n"
            "Activate the virtual environment and run:\n"
            "    pip install -r requirements.txt\n"
        )

    if args.tor:
        setup_tor()

    target = args.pages * 10  # scholarly yields one record at a time

    year_info = ""
    if args.year_low or args.year_high:
        year_info = f" | years: {args.year_low or '?'} – {args.year_high or '?'}"

    print(f"\nSearching Google Scholar for: '{args.keywords}'{year_info}")
    print(f"Target: {args.pages} page(s) (~{target} results)\n")

    query_kwargs = {}
    if args.year_low:
        query_kwargs["year_low"] = args.year_low
    if args.year_high:
        query_kwargs["year_high"] = args.year_high

    query = scholarly.search_pubs(args.keywords, **query_kwargs)

    results = []

    for i, pub in enumerate(query):
        if i >= target:
            break

        bib = pub.get("bib", {})
        title = bib.get("title", "N/A")
        authors = bib.get("author", "N/A")
        year = bib.get("pub_year", "N/A")
        venue = bib.get("venue", "N/A")
        abstract = bib.get("abstract", "") or ""

        if isinstance(authors, list):
            authors = "; ".join(authors)

        url = pub.get("pub_url") or pub.get("eprint_url") or "N/A"

        record = {
            "index":    i + 1,
            "title":    title,
            "authors":  authors,
            "year":     year,
            "venue":    venue,
            "url":      url,
            "abstract": abstract[:300].replace("\n", " "),
        }
        results.append(record)

        page_num = (i // 10) + 1
        print(f"  [{i+1:>3}] (page {page_num}/{args.pages}) {title[:75]}")

        delay = random.uniform(args.min_delay, args.max_delay)
        print(f"       ↳ waiting {delay:.1f}s …")
        time.sleep(delay)

    return results


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
    except Exception as e:
        print(f"\n[ERROR] {e}")
        print(
            "\nCommon causes:\n"
            "  • Google served a CAPTCHA — wait 20-30 min and retry.\n"
            "  • Network issue — check your connection.\n"
            "  • Try running with --tor for better anonymity.\n"
        )
        raise

    elapsed = (datetime.now() - start).seconds
    print(f"  Duration : {elapsed}s")
    print("=" * 65)


if __name__ == "__main__":
    main()
