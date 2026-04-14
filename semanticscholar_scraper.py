import time
import requests

API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

class RateLimitError(Exception):
    pass
PER_PAGE = 25
FIELDS = "title,authors,year,abstract,venue,externalIds,openAccessPdf"


def fetch_page(keywords, offset, year_low=None, year_high=None):
    params = {
        "query":  keywords,
        "fields": FIELDS,
        "limit":  PER_PAGE,
        "offset": offset,
    }
    if year_low or year_high:
        low  = year_low  or 1900
        high = year_high or 2099
        params["year"] = f"{low}-{high}"

    headers = {"User-Agent": "papers-scraper/1.0"}
    try:
        response = requests.get(API_URL, params=params, headers=headers, timeout=20)
        if response.status_code == 429:
            raise RateLimitError()
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        raise RuntimeError("Semantic Scholar API timed out. Try fewer pages or check your connection.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Could not reach Semantic Scholar API. Check your internet connection.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"Semantic Scholar API returned an error: {e}")


def parse_results(data, index_start):
    records = []
    for i, paper in enumerate(data.get("data", [])):
        title   = paper.get("title") or "N/A"

        authors_list = paper.get("authors", [])
        authors = "; ".join(a.get("name", "") for a in authors_list if a.get("name")) or "N/A"

        year  = paper.get("year") or "N/A"
        venue = paper.get("venue") or "N/A"

        ext_ids = paper.get("externalIds") or {}
        doi     = ext_ids.get("DOI")
        oa_pdf  = (paper.get("openAccessPdf") or {}).get("url")
        url     = f"https://doi.org/{doi}" if doi else oa_pdf or "N/A"

        abstract = (paper.get("abstract") or "")[:300]

        records.append({
            "index":    index_start + i,
            "title":    title,
            "authors":  authors,
            "year":     year,
            "venue":    venue,
            "url":      url,
            "abstract": abstract,
        })
    return records


def scrape_pages(keywords, pages, year_low=None, year_high=None):
    for page in range(pages):
        offset  = page * PER_PAGE
        data    = fetch_page(keywords, offset, year_low, year_high)
        papers  = data.get("data", [])
        if not papers:
            return
        yield page + 1, papers, data.get("total", 0)
        if page < pages - 1:
            time.sleep(2)


def run_scrape(keywords, pages, year_low=None, year_high=None):
    all_results = []
    index = 1
    for _, papers, _ in scrape_pages(keywords, pages, year_low, year_high):
        records = parse_results({"data": papers}, index)
        all_results.extend(records)
        index += len(records)
    return all_results
