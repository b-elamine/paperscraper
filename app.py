import csv
import io

from flask import Flask, Response, render_template, request, jsonify

from scraper import run_scrape

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/scrape", methods=["POST"])
def scrape():
    keywords = request.form.get("keywords", "").strip()
    if not keywords:
        return jsonify({"error": "Keywords are required."}), 400

    try:
        pages    = int(request.form.get("pages", 10))
        year_low = request.form.get("year_low", "").strip() or None
        year_high= request.form.get("year_high", "").strip() or None
        # Use provided region or fall back to browser's Accept-Language
        lang = request.form.get("lang", "").strip()
        if not lang:
            lang = request.accept_languages.best[0][:2] if request.accept_languages else "en"

        pages    = max(1, min(pages, 100))
        year_low = int(year_low)  if year_low  else None
        year_high= int(year_high) if year_high else None
    except ValueError as e:
        return jsonify({"error": f"Invalid input: {e}"}), 400

    try:
        records = run_scrape(
            keywords=keywords,
            pages=pages,
            lang=lang,
            year_low=year_low,
            year_high=year_high,
        )
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": f"Scraping failed: {e}"}), 500

    if not records:
        return jsonify({"error": "No results found. Try different keywords or a wider year range."}), 404

    # Build CSV in memory
    output = io.StringIO()
    fieldnames = ["index", "title", "authors", "year", "venue", "url", "abstract"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(records)
    output.seek(0)

    safe_name = keywords.replace(" ", "_")[:40]
    filename  = f"scholar_{safe_name}.csv"

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


if __name__ == "__main__":
    app.run(debug=True)
