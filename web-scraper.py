import argparse
import csv
import sys
from datetime import datetime

from scraper import detect_lang, run_scrape


def parse_args():
    parser = argparse.ArgumentParser(
        description="Scrape Google Scholar papers by keyword.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("-k", "--keywords", required=True,
                        help="Search query / keywords")
    parser.add_argument("-p", "--pages", type=int, default=10, metavar="N",
                        help="Number of pages (10 results/page, default: 10)")
    parser.add_argument("--year-low",  type=int, default=None, dest="year_low",
                        help="Filter from this year onward")
    parser.add_argument("--year-high", type=int, default=None, dest="year_high",
                        help="Filter up to this year")
    parser.add_argument("--lang", default=None,
                        help="Language code, e.g. fr, en (auto-detected if not set)")
    parser.add_argument("-o", "--output", default="scholar_results.csv",
                        help="Output CSV filename (default: scholar_results.csv)")
    parser.add_argument("--min-delay", type=float, default=3.0, dest="min_delay",
                        help="Min seconds between pages (default: 3)")
    parser.add_argument("--max-delay", type=float, default=6.0, dest="max_delay",
                        help="Max seconds between pages (default: 6)")
    return parser.parse_args()


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


def main():
    args = parse_args()

    if args.pages < 1 or args.pages > 100:
        sys.exit("[ERROR] --pages must be between 1 and 100.")
    if args.min_delay > args.max_delay:
        sys.exit("[ERROR] --min-delay cannot be greater than --max-delay.")

    lang = args.lang or detect_lang()

    year_info = ""
    if args.year_low or args.year_high:
        year_info = f" | years: {args.year_low or '?'} – {args.year_high or '?'}"

    start = datetime.now()
    print("=" * 65)
    print("  Google Scholar Scraper")
    print(f"  Started : {start.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)
    print(f"\nSearching for: '{args.keywords}'{year_info}")
    print(f"Locale: {lang} | Target: {args.pages} page(s) (~{args.pages * 10} results)\n")

    try:
        records = run_scrape(
            keywords=args.keywords,
            pages=args.pages,
            lang=lang,
            year_low=args.year_low,
            year_high=args.year_high,
            min_delay=args.min_delay,
            max_delay=args.max_delay,
        )
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
