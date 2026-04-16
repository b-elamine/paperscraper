import locale
import random
import time

from scholarly import scholarly
import scholarly._scholarly as _sch


def detect_lang():
    try:
        code = locale.getlocale()[0] or ""
        lang = code.split("_")[0]
        return lang if len(lang) == 2 else "en"
    except Exception:
        return "en"



def _pub_to_record(pub):
    bib     = pub.get("bib", {})
    authors = bib.get("author", "N/A")
    if isinstance(authors, list):
        authors = ", ".join(authors)
    elif not authors:
        authors = "N/A"

    year    = bib.get("pub_year", "N/A") or "N/A"
    venue   = bib.get("venue",    "N/A") or "N/A"
    url     = pub.get("pub_url",  "N/A") or "N/A"
    abstract = (bib.get("abstract", "") or "")[:300]

    return {
        "title":    bib.get("title", "N/A") or "N/A",
        "authors":  authors,
        "year":     str(year),
        "venue":    venue,
        "url":      url,
        "abstract": abstract,
    }


def scrape_pages(keywords, pages, lang=None, year_low=None, year_high=None,
                 min_delay=8.0, max_delay=12.0):
    """
    Generator that yields (page_num, records) one page at a time.

    Uses the scholarly library for proper browser fingerprinting.
    Delay happens AFTER yielding so the caller can stream data before waiting.

    For sessions longer than ~15 pages on a cloud/server IP, call
    setup_free_proxies() before this function to enable IP rotation.

    Delays are intentionally 20-35 s, shorter delays trigger blocks.
    """
    # Patch scholarly's hardcoded hl=en to respect the user's language
    hl = lang if lang else "en"
    _sch._PUBSEARCH = f"/scholar?hl={hl}&q={{0}}"

    search_iter = scholarly.search_pubs(
        keywords,
        patents=False,          # exclude patents for academic use
        year_low=year_low,
        year_high=year_high,
    )

    page_num = 0
    batch    = []

    try:
        for pub in search_iter:
            batch.append(_pub_to_record(pub))

            if len(batch) == 10:
                page_num += 1
                yield page_num, batch
                batch = []

                if page_num >= pages:
                    return

                # Wait between pages, this is critical to avoid blocks.
                # The sleep happens BEFORE scholarly fetches the next page.
                time.sleep(random.uniform(min_delay, max_delay))

    except Exception as exc:
        msg = str(exc).lower()
        if "captcha" in msg or "blocked" in msg or "too many" in msg or "429" in msg:
            raise RuntimeError(
                "Google Scholar has blocked this IP. "
                "Wait 30–60 minutes and try again with fewer pages."
            ) from exc
        raise

    # Yield any partial last page (fewer than 10 results, end of results)
    if batch and page_num < pages:
        yield page_num + 1, batch


def run_scrape(keywords, pages, lang=None, year_low=None, year_high=None,
               min_delay=8.0, max_delay=12.0):
    all_results = []
    index       = 1
    for _, records in scrape_pages(keywords, pages, lang, year_low, year_high,
                                   min_delay, max_delay):
        for record in records:
            record["index"] = index
            all_results.append(record)
            index += 1
    return all_results
