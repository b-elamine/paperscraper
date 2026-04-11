# Google Scholar Scraper

A command-line tool to scrape papers from Google Scholar by keyword. Extracts title, authors, publication year, venue, and URL into a CSV file.

---

## Setup (run once)

```bash
bash setup.sh
```

creates a `.venv` and installs all dependencies automatically.

---

## Activation

```bash
source .venv/bin/activate
```

---

## Usage

```bash
python web-scraper.py -k "your keywords" -p <number_of_pages>
```

### Arguments

| Argument | Required | Description | Default |
|---|---|---|---|
| `-k` / `--keywords` | Yes | Search query | — |
| `-p` / `--pages` | No | Number of pages to scrape (10 results/page) | `10` |
| `--year-low` | No | Filter results from this year onward | none |
| `--year-high` | No | Filter results up to this year | none |
| `-o` / `--output` | No | Output CSV filename | `scholar_results.csv` |
| `--min-delay` | No | Min seconds between requests | `8` |
| `--max-delay` | No | Max seconds between requests | `15` |
| `--tor` | No | Route traffic through Tor (requires Tor installed) | off |

---

## Examples

```bash
# Scrape 5 pages (~50 results) for "machine learning"
python web-scraper.py -k "machine learning" -p 5

# Scrape with a year range filter
python web-scraper.py -k "sobriété informatique" -p 10 --year-low 2020 --year-high 2024

# Save results to a custom file
python web-scraper.py -k "deep learning" -p 20 -o deep_learning.csv

# Use Tor for anonymity
python web-scraper.py -k "neural networks" -p 15 --tor

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
