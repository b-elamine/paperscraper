import csv
import io
import json
import base64

from flask import Flask, Response, render_template, request, jsonify, stream_with_context

from scraper import run_scrape, scrape_pages as scholar_scrape_pages
from openalex_scraper import scrape_pages as openalex_scrape_pages, parse_results as openalex_parse_results
from semanticscholar_scraper import scrape_pages as semantic_scrape_pages, parse_results as semantic_parse_results, RateLimitError

app = Flask(__name__)


def get_lang(form_lang):
    lang = form_lang.strip() if form_lang else ""
    if not lang:
        lang = request.accept_languages.best[0][:2] if request.accept_languages else "en"
    return lang


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/scrape-stream")
def scrape_stream():
    source    = request.args.get("source", "scholar").strip().lower()
    keywords  = request.args.get("keywords", "").strip()
    pages     = max(1, min(int(request.args.get("pages", 5)), 100))
    year_low  = request.args.get("year_low",  "").strip() or None
    year_high = request.args.get("year_high", "").strip() or None

    year_low  = int(year_low)  if year_low  else None
    year_high = int(year_high) if year_high else None

    if source == "openalex":
        return Response(
            stream_with_context(_stream_openalex(keywords, pages, year_low, year_high)),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    if source == "semanticscholar":
        return Response(
            stream_with_context(_stream_semantic(keywords, pages, year_low, year_high)),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    lang = get_lang(request.args.get("lang", ""))
    return Response(
        stream_with_context(_stream_scholar(keywords, pages, lang, year_low, year_high)),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _stream_scholar(keywords, pages, lang, year_low, year_high):
    all_results = []
    index = 1
    try:
        for page_num, records in scholar_scrape_pages(keywords, pages, lang, year_low, year_high):
            for record in records:
                record["index"] = index
                all_results.append(record)
                index += 1
                yield f"data: {json.dumps({'type': 'paper', 'page': page_num, 'total': pages, 'title': record['title'], 'count': len(all_results)})}\n\n"

        if not all_results:
            yield f"data: {json.dumps({'type': 'error', 'message': 'No results found. Try different keywords or a wider year range.'})}\n\n"
            return

        output = io.StringIO()
        fieldnames = ["index", "title", "authors", "year", "venue", "url", "abstract"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)
        csv_b64   = base64.b64encode(output.getvalue().encode()).decode()
        safe_name = keywords.replace(" ", "_")[:40]
        yield f"data: {json.dumps({'type': 'done', 'csv': csv_b64, 'filename': f'scholar_{safe_name}.csv', 'count': len(all_results)})}\n\n"

    except RuntimeError as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': f'Scraping failed: {e}'})}\n\n"


def _stream_openalex(keywords, pages, year_low, year_high):
    all_results = []
    index = 1
    try:
        for page_num, results, total in openalex_scrape_pages(keywords, pages, year_low, year_high):
            records = openalex_parse_results({"results": results}, index)
            for record in records:
                all_results.append(record)
                index += 1
                yield f"data: {json.dumps({'type': 'paper', 'page': page_num, 'total': pages, 'title': record['title'], 'count': len(all_results)})}\n\n"
            # SSE keepalive comment - prevents proxies from closing the idle connection
            # while the next page is being fetched from the OpenAlex API
            yield ": keepalive\n\n"

        if not all_results:
            yield f"data: {json.dumps({'type': 'error', 'message': 'No results found. Try different keywords or a wider year range.'})}\n\n"
            return

        output = io.StringIO()
        fieldnames = ["index", "title", "authors", "year", "venue", "url", "abstract"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)
        csv_b64   = base64.b64encode(output.getvalue().encode()).decode()
        safe_name = keywords.replace(" ", "_")[:40]
        yield f"data: {json.dumps({'type': 'done', 'csv': csv_b64, 'filename': f'openalex_{safe_name}.csv', 'count': len(all_results)})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': f'Scraping failed: {e}'})}\n\n"


def _stream_semantic(keywords, pages, year_low, year_high):
    all_results = []
    index = 1
    try:
        for page_num, papers, total in semantic_scrape_pages(keywords, pages, year_low, year_high):
            records = semantic_parse_results({"data": papers}, index)
            for record in records:
                all_results.append(record)
                index += 1
                yield f"data: {json.dumps({'type': 'paper', 'page': page_num, 'total': pages, 'title': record['title'], 'count': len(all_results)})}\n\n"
            yield ": keepalive\n\n"

        if not all_results:
            yield f"data: {json.dumps({'type': 'error', 'message': 'No results found. Try different keywords or a wider year range.'})}\n\n"
            return

        output = io.StringIO()
        fieldnames = ["index", "title", "authors", "year", "venue", "url", "abstract"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)
        csv_b64   = base64.b64encode(output.getvalue().encode()).decode()
        safe_name = keywords.replace(" ", "_")[:40]
        yield f"data: {json.dumps({'type': 'done', 'csv': csv_b64, 'filename': f'semantic_{safe_name}.csv', 'count': len(all_results)})}\n\n"

    except RateLimitError:
        yield f"data: {json.dumps({'type': 'error', 'message': 'Semantic Scholar rate limit hit. Wait about a minute and try again.'})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': f'Scraping failed: {e}'})}\n\n"


if __name__ == "__main__":
    app.run(debug=True)
