import math
from datetime import date
from statistics import mean, median

CURRENT_YEAR = date.today().year


def _parse_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _author_count(authors_str):
    if not authors_str or authors_str == "N/A":
        return 1
    parts = [a.strip() for a in authors_str.split(";") if a.strip()]
    return max(1, len(parts))


def _paper_age(year_val):
    y = _parse_int(year_val)
    if y and 1900 <= y <= CURRENT_YEAR:
        return max(1, CURRENT_YEAR - y + 1)
    return None


def calculate_metrics(papers):
    """
    Calculate bibliometric metrics from a list of paper dicts.

    Expected fields per paper (all optional except title):
        title, authors, year, citation_count, reference_count, influential_citations

    Returns a dict with three metric tiers:
        core       — requires citation_count (all sources)
        reference  — requires reference_count (OpenAlex, Semantic Scholar)
        advanced   — requires influential_citations (Semantic Scholar only)

    Metrics not calculable due to missing data are absent from the result.
    """
    if not papers:
        return {"paper_count": 0}

    n = len(papers)

    has_citations    = any(_parse_int(p.get("citation_count")) is not None for p in papers)
    has_references   = any(_parse_int(p.get("reference_count")) is not None for p in papers)
    has_influential  = any(_parse_int(p.get("influential_citations")) is not None for p in papers)
    has_year         = any(_paper_age(p.get("year")) is not None for p in papers)
    has_authors      = any(p.get("authors") not in (None, "N/A", "") for p in papers)

    result = {
        "paper_count": n,
        "available_tiers": {
            "core":      has_citations,
            "reference": has_references,
            "advanced":  has_influential,
        },
    }

    # ── CORE METRICS ─────────────────────────────────────────────────────────
    if has_citations:
        citations = [_parse_int(p.get("citation_count")) or 0 for p in papers]
        cites_desc = sorted(citations, reverse=True)
        total_cites = sum(citations)

        result["total_citations"]  = total_cites
        result["mean_citations"]   = round(total_cites / n, 2)
        result["median_citations"] = median(citations)
        result["max_citations"]    = cites_desc[0]
        result["uncited_count"]    = citations.count(0)
        result["uncited_rate_pct"] = round(citations.count(0) / n * 100, 1)

        # H-index
        h = sum(c >= i + 1 for i, c in enumerate(cites_desc))
        result["h_index"] = h

        # G-index
        g, cumsum = 0, 0
        for i, c in enumerate(cites_desc):
            cumsum += c
            if cumsum >= (i + 1) ** 2:
                g = i + 1
        result["g_index"] = g

        # E-index
        excess = sum(cites_desc[:h]) - h ** 2
        result["e_index"] = round(math.sqrt(excess), 2) if excess > 0 else 0

        # Top cited thresholds
        if n >= 10:
            result["top_10pct_min_cites"] = cites_desc[max(0, math.ceil(n * 0.10) - 1)]
        if n >= 100:
            result["top_1pct_min_cites"] = cites_desc[max(0, math.ceil(n * 0.01) - 1)]

        # Author-normalized metrics
        if has_authors:
            author_counts = [_author_count(p.get("authors")) for p in papers]
            avg_authors = mean(author_counts)
            result["collaboration_index"] = round(avg_authors, 2)

            # HI-index = h / avg_authors_per_paper
            result["hi_index"] = round(h / avg_authors, 2) if avg_authors else None

            # HI-norm: h-index on per-author normalized citation counts
            norm = sorted([c / ac for c, ac in zip(citations, author_counts)], reverse=True)
            result["hi_norm"] = sum(c >= i + 1 for i, c in enumerate(norm))

        # Year-based metrics
        if has_year:
            ages = [_paper_age(p.get("year")) for p in papers]
            valid_years = [
                _parse_int(p.get("year")) for p in papers
                if _paper_age(p.get("year")) is not None
            ]
            if valid_years:
                span = CURRENT_YEAR - min(valid_years) + 1
                result["year_span"]    = span
                result["oldest_year"]  = min(valid_years)
                result["newest_year"]  = max(valid_years)
                result["cites_per_year"] = round(total_cites / span, 2)

            # AWCR and AW-index
            awcr = sum(
                c / age
                for c, age in zip(citations, ages)
                if age is not None
            )
            result["awcr"]     = round(awcr, 2)
            result["aw_index"] = round(math.sqrt(awcr), 2)

    # ── REFERENCE METRICS ────────────────────────────────────────────────────
    if has_references:
        refs = [_parse_int(p.get("reference_count")) or 0 for p in papers]
        result["total_references"]  = sum(refs)
        result["mean_references"]   = round(mean(refs), 2)
        result["median_references"] = median(refs)

    # ── ADVANCED METRICS ─────────────────────────────────────────────────────
    if has_influential:
        infl = [_parse_int(p.get("influential_citations")) or 0 for p in papers]
        total_infl = sum(infl)
        result["total_influential_citations"] = total_infl
        result["mean_influential_citations"]  = round(mean(infl), 2)
        if has_citations and result.get("total_citations", 0) > 0:
            result["influential_citation_ratio_pct"] = round(
                total_infl / result["total_citations"] * 100, 1
            )

    return result
