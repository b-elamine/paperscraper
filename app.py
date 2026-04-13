import csv
import io
import json
import base64

from flask import Flask, Response, render_template, request, jsonify

from scraper import run_scrape, scrape_pages

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
    keywords  = request.args.get("keywords", "").strip()
    pages     = max(1, min(int(request.args.get("pages", 10)), 100))
    year_low  = request.args.get("year_low",  "").strip() or None
    year_high = request.args.get("year_high", "").strip() or None
    lang      = get_lang(request.args.get("lang", ""))

    year_low  = int(year_low)  if year_low  else None
    year_high = int(year_high) if year_high else None

    def generate():
        all_results = []
        index = 1
        try:
            for page_num, records in scrape_pages(keywords, pages, lang, year_low, year_high):
                for record in records:
                    record["index"] = index
                    all_results.append(record)
                    index += 1
                    yield f"data: {json.dumps({'type': 'paper', 'page': page_num, 'total': pages, 'title': record['title'], 'count': len(all_results)})}\n\n"

            if not all_results:
                yield f"data: {json.dumps({'type': 'error', 'message': 'No results found. Try different keywords or a wider year range.'})}\n\n"
                return

            # Build CSV and encode as base64 to send in the final event
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

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


if __name__ == "__main__":
    app.run(debug=True)
