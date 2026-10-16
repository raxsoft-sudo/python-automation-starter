# Scrape quotes.toscrape.com step by step (Python, CSS selectors, CSV and JSON)

`quotes.toscrape.com` is a public sandbox made for scraping practice. This guide goes from nothing to a clean CSV of quotes using `scraper/static_list_scraper.py`.

## Step 1. Install

```bash
cd scraper
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Step 2. Inspect the page

Each quote is a `div.quote` containing:

- `span.text`: the quote
- `small.author`: author name
- `span a`: link to the author page
- `div.tags`: the tags, with individual tags as `a.tag`

## Step 3. First config

The repo ships `configs/quotes.json`:

```json
{
  "item": "div.quote",
  "fields": {
    "text": "span.text",
    "author": "small.author",
    "tags": "div.tags",
    "author_url": "span a@href"
  }
}
```

(The shipped file also has a `"next"` key. `static_list_scraper.py` ignores it because it reads only the one page you give it.)

```bash
python static_list_scraper.py https://quotes.toscrape.com/ -c configs/quotes.json -o quotes.csv
```

Result: `INFO Wrote 10 rows to quotes.csv`. Real first rows:

```
text,author,tags,author_url
“The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking.”,Albert Einstein,Tags: change deep-thoughts thinking world,https://quotes.toscrape.com/author/Albert-Einstein
"“It is our choices, Harry, that show what we truly are, far more than our abilities.”",J.K. Rowling,Tags: abilities choices,https://quotes.toscrape.com/author/J-K-Rowling
```

Two things to improve: the tags column starts with the label "Tags:", and the quotes include curly quote characters.

## Step 4. Cleaner tags

Each quote has a `<meta class="keywords" content="...">` with a comma-separated tag list. Use it:

```json
{
  "item": "div.quote",
  "fields": {
    "text": "span.text",
    "author": "small.author",
    "tags": "meta.keywords@content",
    "author_url": "span a@href"
  }
}
```

Save as `configs/quotes_clean.json` and run on page 2:

```bash
python static_list_scraper.py https://quotes.toscrape.com/page/2/ -c configs/quotes_clean.json -o quotes_p2.csv
```

Real result: 10 rows, for example Marilyn Monroe with tags `friends,heartbreak,inspirational,life,love,sisters`, and J.K. Rowling with tags `courage,friends`.

## Step 5. JSON instead of CSV

Just change the extension:

```bash
python static_list_scraper.py https://quotes.toscrape.com/ -c configs/quotes_clean.json -o quotes.json
```

Each element looks like:

```json
{
  "text": "“The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking.”",
  "author": "Albert Einstein",
  "tags": "change,deep-thoughts,thinking,world",
  "author_url": "https://quotes.toscrape.com/author/Albert-Einstein"
}
```

## Step 6. Get several pages

This script fetches the URL you give it. The site has pages `/page/1/` to `/page/10/`. Loop in the shell:

```bash
for i in 1 2 3; do
  python static_list_scraper.py "https://quotes.toscrape.com/page/$i/" -c configs/quotes_clean.json -o "quotes_p$i.csv"
done
```

Merge them with Python:

```python
import glob
import pandas as pd

df = pd.concat([pd.read_csv(f, encoding="utf-8-sig") for f in sorted(glob.glob("quotes_p*.csv"))])
df.to_csv("quotes_all.csv", index=False, encoding="utf-8-sig")
print(len(df))
```

A crawler that follows the "Next" link until the end is a separate script, not part of `static_list_scraper.py`.

## Common errors

- **`No items matched selector 'div.quote'`**: wrong page. Check the URL.
- **Curly quotes look garbled in Excel**: open the CSV through Data > From Text/CSV and choose UTF-8, or see [guide 09](09-scraped-csv-to-clean-excel.md). The files are written with a UTF-8 byte-order mark, so a plain double-click normally works.
- **`ModuleNotFoundError: No module named 'bs4'`**: run `pip install -r requirements.txt` in the active environment.
- **File not found for the config**: `configs/quotes.json` is relative to `scraper/`; run from that folder.
- **Only 10 rows**: that is one page of the site. Loop over pages as in Step 6.

---
Need the full kit (15 blocks: Discord bots, paginated & Selenium scrapers, RSS collector, pandas cleaner, OpenAPI + Postman)? **Automation Script Pack — $39:** https://raxsoft.gumroad.com/l/fkits
