# Google Scholar Scraper

A tool to scrape papers from Google Scholar by keyword. You can use it two ways: from the command line or through a web interface. Both give you a CSV file with the paper title, authors, publication year, venue, and URL.

---

## Option 1 - Web Interface

If you just want to search without touching the terminal, a web interface is available at:

```
https://papers-scraper.onrender.com
```

Fill in your keywords, pick how many pages you want, optionally set a year range, and hit the button. The CSV file downloads automatically when the scraping is done.

> The app is hosted on Render free tier so it may take around 30 seconds to wake up on the first request.

---

## Option 2 - Command Line

### Setup (run once)

```bash
bash setup.sh
```

This creates a `.venv` and installs all dependencies automatically.

### Activation

At the start of each new terminal session, activate the environment:

```bash
source .venv/bin/activate
```

### Usage

```bash
python web-scraper.py -k "your keywords" -p <number_of_pages>
```

### Arguments

| Argument | Required | Description | Default |
|---|---|---|---|
| `-k` / `--keywords` | Yes | Search query | none |
| `-p` / `--pages` | No | Number of pages to scrape (10 results/page) | `10` |
| `--year-low` | No | Filter results from this year onward | none |
| `--year-high` | No | Filter results up to this year | none |
| `--lang` | No | Language code for Scholar (e.g. fr, en) | auto-detected |
| `-o` / `--output` | No | Output CSV filename | `scholar_results.csv` |
| `--min-delay` | No | Min seconds between pages | `3` |
| `--max-delay` | No | Max seconds between pages | `6` |

### Examples

```bash
# Scrape 5 pages (~50 results) for "machine learning"
python web-scraper.py -k "machine learning" -p 5

# Scrape with a year range filter
python web-scraper.py -k "sobriété informatique" -p 10 --year-low 2020 --year-high 2024

# Force a specific language
python web-scraper.py -k "secure deployment" -p 5 --lang fr

# Save results to a custom file
python web-scraper.py -k "deep learning" -p 20 -o deep_learning.csv

# Show all available options
python web-scraper.py --help
```

---

## Output

Results are saved as a CSV file with the following columns:

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

## Run the Web Interface Locally

If you want to run the web app on your own machine instead of using the hosted version:

```bash
source .venv/bin/activate
python app.py
```

Then open `http://127.0.0.1:5000` in your browser.

---

## Tips

- If Google blocks the scraper with a CAPTCHA, wait 20 to 30 minutes and try again.
- Avoid running too many pages in a short time, it increases the chance of getting blocked.
- The language is auto-detected from your system locale. If results look off, pass `--lang` explicitly.
