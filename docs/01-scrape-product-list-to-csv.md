# How to scrape a product list to CSV with Python (robots.txt-safe)

This guide scrapes the first page of a product listing into a CSV file using `scraper/static_list_scraper.py`. The script checks `robots.txt` before fetching, waits between requests, retries on temporary errors, and writes CSV or JSON depending on the output file extension. We use `books.toscrape.com`, a public practice shop built for scraping.

## 1. Install

```bash
cd scraper
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

The requirements are only `requests` and `beautifulsoup4`.

## 2. Look at the page

Open https://books.toscrape.com/ in your browser, right-click a book, and choose Inspect. Each book is an `<article class="product_pod">`. Inside it:

- the title is the `title` attribute of the link inside `<h3>`
- the price is `<p class="price_color">`
- the stock text is `<p class="availability">`
- the product link is the `href` of the same `<h3>` link

## 3. Write the config

The scraper reads a JSON file with one `item` selector (the repeated block) and a `fields` map of column name to selector. A selector ending in `@attr` reads that attribute instead of the text. `href` and `src` values are converted to absolute URLs. Save this as `configs/books.json`:

```json
{
  "item": "article.product_pod",
  "fields": {
    "title": "h3 a@title",
    "price": "p.price_color",
    "availability": "p.availability",
    "url": "h3 a@href"
  }
}
```

## 4. Run it

```bash
python static_list_scraper.py https://books.toscrape.com/ -c configs/books.json -o books.csv
```

Output on the run used for this guide:

```
INFO Wrote 20 rows to books.csv
```

First rows of `books.csv`:

```
title,price,availability,url
A Light in the Attic,Â£51.77,In stock,https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html
Tipping the Velvet,Â£53.74,In stock,https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html
Soumission,Â£50.10,In stock,https://books.toscrape.com/catalogue/soumission_998/index.html
```

Note the `Â£` in the price column. That is an encoding problem, not a selector problem, and it is fixed in [guide 07](07-scrape-books-prices-to-csv.md) and [guide 09](09-scraped-csv-to-clean-excel.md).

## 5. Useful flags

| Flag | Meaning | Default |
|---|---|---|
| `-o`, `--output` | Output file, `.csv` or `.json` | `output.csv` |
| `--delay` | Seconds between requests | 1.0 |
| `--retries` | Retries per request | 3 |
| `--backoff` | Exponential backoff base | 2.0 |
| `--timeout` | Request timeout in seconds | 20 |
| `--user-agent` | Your own User-Agent string | built-in placeholder |
| `--ignore-robots` | Skip the robots.txt check (not recommended) | off |
| `-v`, `--verbose` | Debug logging | off |

Set a User-Agent that identifies you, for example:

```bash
python static_list_scraper.py https://books.toscrape.com/ -c configs/books.json -o books.csv \
  --user-agent "MyScraper/1.0 (contact: me@example.org)"
```

## Common errors

- **`WARNING No items matched selector 'article.product_pod'`**: the `item` selector found nothing. Either the page is a different one (running the books config against quotes.toscrape.com gives this warning and an empty file), or the content is loaded by JavaScript, which this script cannot see.
- **`ERROR Bad config ...`**: the config file path is wrong or the JSON is invalid (trailing commas are the usual cause). The script exits with code 2 here.
- **`Blocked by robots.txt, skipping`**: the site disallows that path for your User-Agent. Do not work around it; pick another source or ask the site owner.
- **`GET ... failed: HTTP 404 (not retrying)`**: wrong URL. 4xx errors other than 429 are not retried.
- **Empty cells in one column**: that field's selector did not match inside some items; the script writes an empty string instead of failing.

---
Need the full kit (15 blocks: Discord bots, paginated & Selenium scrapers, RSS collector, pandas cleaner, OpenAPI + Postman)? **Automation Script Pack — $39:** https://raxsoft.gumroad.com/l/fkits
