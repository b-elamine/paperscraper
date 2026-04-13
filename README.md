# Papers Scraper

A tool to search academic papers by keyword and export the results as a CSV. It supports two sources: **Google Scholar** (web scraping) and **OpenAlex** (free open API). You can use it from a web interface or straight from the command line.

Both sources give you the same output format: title, authors, year, venue, URL, and abstract.

---

## Web Interface

If you don't want to touch the terminal, the hosted version is at:

```
https://papers-scraper.onrender.com
```

Pick your source (Scholar or OpenAlex), enter your keywords, set a year range if you want, and hit the button. The CSV downloads automatically when it's done.

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

### Google Scholar CLI

```bash
python web-scraper.py -k "your keywords" -p <pages>
```

| Argument | Required | Description | Default |
|---|---|---|---|
| `-k` / `--keywords` | Yes | Search query | |
| `-p` / `--pages` | No | Pages to scrape (10 results/page) | `10` |
| `--year-low` | No | Filter from this year | |
| `--year-high` | No | Filter up to this year | |
| `--lang` | No | Scholar language code (e.g. `fr`, `en`) | auto-detected |
| `-o` / `--output` | No | Output CSV filename | `scholar_results.csv` |
| `--min-delay` | No | Min seconds between pages | `3` |
| `--max-delay` | No | Max seconds between pages | `6` |

**Examples:**

```bash
# Basic search, 5 pages (~50 results)
python web-scraper.py -k "machine learning" -p 5

# With a year range
python web-scraper.py -k "sobriété informatique" -p 10 --year-low 2020 --year-high 2024

# Force a specific language
python web-scraper.py -k "secure deployment" -p 5 --lang fr

# Save to a custom file
python web-scraper.py -k "deep learning" -p 20 -o deep_learning.csv
```

> **Heads up:** Google Scholar is web scraping. Google can flag requests, serve a CAPTCHA, or block the server temporarily. If that happens, wait 30–60 minutes and try again. Avoid hammering too many pages at once.

---

### OpenAlex CLI

```bash
python openalex-scraper.py -k "your keywords" -p <pages>
```

| Argument | Required | Description | Default |
|---|---|---|---|
| `-k` / `--keywords` | Yes | Search query | |
| `-p` / `--pages` | No | Pages to fetch (25 results/page) | `5` |
| `--year-low` | No | Filter from this year | |
| `--year-high` | No | Filter up to this year | |
| `-o` / `--output` | No | Output CSV filename | `openalex_results.csv` |

**Examples:**

```bash
# Basic search, 5 pages (~125 results)
python openalex-scraper.py -k "machine learning" -p 5

# With a year range
python openalex-scraper.py -k "deep learning" -p 10 --year-low 2020 --year-high 2024

# Save to a custom file
python openalex-scraper.py -k "network security" -p 3 -o results.csv
```

> OpenAlex pulls from a free open API, no scraping, no blocks, no CAPTCHA. Safe to use freely.

---

## Output format

Both sources produce the same CSV columns:

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
