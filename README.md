# Papers Scraper

search academic papers by keyword and get a CSV with title, authors, year, venue, URL and abstract.

two ways to use it: the web interface or the command line. sources depend on which one you pick.

---

## Web interface

hosted at:

```
https://paperpull.app/
```

two sources available in the UI:

- **OpenAlex** - open API, 250M+ papers, fast and reliable
- **Google Scholar** - actual scraping, slower but hits Scholar directly. goes at 8-12s per page to avoid blocks, so 40 pages takes around 7 minutes. if Google blocks it, just wait 30 min and retry. you can also set a language code (fr, en, ar...) to tune the results to your region.

pick your source, type your keywords, set a year range if you want, hit search. CSV downloads automatically when done. works on mobile too.

> if Google Scholar gets blocked on the hosted version, it is because the server IP is shared. running it locally on your own machine works much better for Scholar, see below.

---

## Command line

three sources available in the CLI: `scholar`, `openalex`, `semanticscholar`.

### setup (run once)

```bash
./setup.sh
source .venv/bin/activate
```

### usage

```bash
python web-scraper.py -s scholar         -k "your keywords" -p <pages>
python web-scraper.py -s openalex        -k "your keywords" -p <pages>
python web-scraper.py -s semanticscholar -k "your keywords" -p <pages>
```

default source is `semanticscholar` if you leave out `-s`.

| argument | required | description | default |
|---|---|---|---|
| `-s` / `--source` | no | `scholar`, `openalex`, or `semanticscholar` | `semanticscholar` |
| `-k` / `--keywords` | yes | search query | |
| `-p` / `--pages` | no | pages to fetch (25 results/page, 10 for Scholar) | `10` |
| `--year-low` | no | filter from this year | |
| `--year-high` | no | filter up to this year | |
| `--lang` | no | Scholar only: 2-letter language code (fr, en, ar...) | auto-detected |
| `-o` / `--output` | no | output CSV filename | `<source>_results.csv` |
| `--min-delay` | no | Scholar only: min seconds between pages | `8` |
| `--max-delay` | no | Scholar only: max seconds between pages | `12` |

**examples:**

```bash
# Semantic Scholar, 10 pages (~250 results)
python web-scraper.py -k "machine learning" -p 10

# OpenAlex with a year range
python web-scraper.py -s openalex -k "deep learning" -p 10 --year-low 2020 --year-high 2024

# Google Scholar in French
python web-scraper.py -s scholar -k "sobriete informatique" -p 5 --lang fr

# save to a specific file
python web-scraper.py -s openalex -k "network security" -p 5 -o results.csv
```

> Scholar scrapes Google directly so it can get blocked. if that happens wait 30 min and try again with fewer pages. running it locally on a home connection works much better than on a server.

---

## run locally

```bash
source .venv/bin/activate
python app.py
```

opens at `http://127.0.0.1:5000`. to make it accessible on your local network (phone, other machines):

```bash
python app.py  # already binds to 0.0.0.0
```

then access it at `http://<your-local-ip>:5000` from any device on the same network.

---

## output format

all sources produce the same CSV columns:

| column | description |
|---|---|
| `index` | row number |
| `title` | paper title |
| `authors` | authors (semicolon-separated) |
| `year` | publication year |
| `venue` | journal or conference name |
| `url` | link to the paper |
| `abstract` | abstract excerpt (up to 300 characters) |
