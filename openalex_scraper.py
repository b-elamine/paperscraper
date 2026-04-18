import time
import requests

API_URL = "https://api.openalex.org/works"
PER_PAGE = 25


def reconstruct_abstract(inverted_index):
    if not inverted_index:
        return ""
    words = [""] * (max(pos for positions in inverted_index.values() for pos in positions) + 1)
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words)


def fetch_page(keywords, page, year_low=None, year_high=None):
    params = {
        "search":   keywords,
        "per-page": PER_PAGE,
        "page":     page,
        "select":   "title,authorships,publication_year,primary_location,doi,abstract_inverted_index,cited_by_count,referenced_works_count",
    }
    if year_low or year_high:
        low  = year_low  or 1900
        high = year_high or 2099
        params["filter"] = f"publication_year:{low}-{high}"

    headers = {"User-Agent": "openalex-scraper/1.0 (research tool)"}
    try:
        response = requests.get(API_URL, params=params, headers=headers, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        raise RuntimeError(f"OpenAlex API timed out on page {page}. Try fewer pages or check your connection.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError(f"Could not reach OpenAlex API (page {page}). Check your internet connection.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"OpenAlex API returned an error on page {page}: {e}")


def parse_results(data, index_start):
    records = []
    for i, work in enumerate(data.get("results", [])):
        title = work.get("title") or "N/A"

        authorships = work.get("authorships", [])
        names   = [a.get("author", {}).get("display_name", "") for a in authorships]
        authors = "; ".join(n for n in names if n) or "N/A"

        year  = work.get("publication_year") or "N/A"

        loc   = work.get("primary_location") or {}
        src   = loc.get("source") or {}
        venue = src.get("display_name") or "N/A"

        url   = work.get("doi") or loc.get("landing_page_url") or "N/A"

        abstract = reconstruct_abstract(work.get("abstract_inverted_index"))[:300]

        cited_by = work.get("cited_by_count")
        ref_count = work.get("referenced_works_count")

        records.append({
            "index":                 index_start + i,
            "title":                 title,
            "authors":               authors,
            "year":                  year,
            "venue":                 venue,
            "url":                   url,
            "abstract":              abstract,
            "citation_count":        int(cited_by) if cited_by is not None else None,
            "reference_count":       int(ref_count) if ref_count is not None else None,
            "influential_citations": None,
        })
    return records


def scrape_pages(keywords, pages, year_low=None, year_high=None):
    for page in range(1, pages + 1):
        data    = fetch_page(keywords, page, year_low, year_high)
        results = data.get("results", [])
        if not results:
            return
        yield page, results, data.get("meta", {}).get("count", 0)
        if page < pages:
            time.sleep(0.3)


def run_scrape(keywords, pages, year_low=None, year_high=None):
    all_results = []
    index = 1
    for _, results, _ in scrape_pages(keywords, pages, year_low, year_high):
        records = parse_results({"results": results}, index)
        all_results.extend(records)
        index += len(records)
    return all_results
