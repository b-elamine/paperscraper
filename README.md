# Papers Scraper

A tool to search academic papers by keyword and export the results as a CSV. It supports three sources: **Semantic Scholar**, **OpenAlex**, and **Google Scholar** (CLI only). You can use it from a web interface or straight from the command line.

All sources give you the same output format: title, authors, year, venue, URL, and abstract.

---

## Web Interface

If you don't want to touch the terminal, the hosted version is at:

```
https://papers-scraping.onrender.com/
```

Pick your source (Semantic Scholar or OpenAlex), enter your keywords, set a year range if you want, and hit the button. The CSV downloads automatically when it's done.

> Hosted on Render free tier, it may take ~30 seconds to wake up on the first request.

---

## Command Line

### Setup (run once)

```bash
bash setup.sh
```

Creates a `.venv` and installs everything.

### Activate the environment

```bash
source .venv/bin/activate
```

---

### CLI usage

All three sources go through the same script. Use `-s` to pick one:

```bash
python web-scraper.py -s semanticscholar -k "your keywords" -p <pages>
python web-scraper.py -s openalex        -k "your keywords" -p <pages>
python web-scraper.py -s scholar         -k "your keywords" -p <pages>
```

Default source is `semanticscholar` if you leave out `-s`.

| Argument | Required | Description | Default |
|---|---|---|---|
| `-s` / `--source` | No | `semanticscholar`, `openalex`, or `scholar` | `semanticscholar` |
| `-k` / `--keywords` | Yes | Search query | |
| `-p` / `--pages` | No | Pages to fetch (25 results/page, 10 for Scholar) | `10` |
| `--year-low` | No | Filter from this year | |
| `--year-high` | No | Filter up to this year | |
| `--lang` | No | Scholar only: language code (e.g. `fr`, `en`) | auto-detected |
| `-o` / `--output` | No | Output CSV filename | `<source>_results.csv` |
| `--min-delay` | No | Scholar only: min seconds between pages | `3` |
| `--max-delay` | No | Scholar only: max seconds between pages | `6` |

**Examples:**

```bash
# Semantic Scholar, 10 pages (~250 results)
python web-scraper.py -k "machine learning" -p 10

# OpenAlex with a year range
python web-scraper.py -s openalex -k "deep learning" -p 10 --year-low 2020 --year-high 2024

# Google Scholar, force French language
python web-scraper.py -s scholar -k "sobriété informatique" -p 5 --lang fr

# Save to a custom file
python web-scraper.py -s semanticscholar -k "network security" -p 5 -o results.csv
```

> **Heads up (Scholar only):** Google Scholar is web scraping. Google can flag requests, serve a CAPTCHA, or block the server temporarily. If that happens, wait 30 to 60 minutes and try again. Avoid hammering too many pages at once.

---

## Output format

All sources produce the same CSV columns:

| Column | Description |
|---|---|
| `index` | Row number |
| `title` | Paper title |
| `authors` | Authors (semicolon-separated) |
| `year` | Publication year |
| `venue` | Journal or conference name |
| `url` | Link to the paper |
| `abstract` | Abstract excerpt (up to 300 characters) |

---

## Run the web app locally

```bash
source .venv/bin/activate
python app.py
```

Then open `http://127.0.0.1:5000`.
