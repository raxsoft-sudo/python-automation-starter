# How to extract links and titles from a web page into JSON with Python

Sometimes you only want a clean list of links: the text a visitor sees and the URL it points to. With `static_list_scraper.py` you can do this without writing code, because a selector may be empty (meaning "the item itself") and may end with `@href`.

## 1. The trick: empty selector means "the element itself"

In the scraper, each field is split at `@`. If the part before `@` is empty, the field is read from the matched item itself. So for an item selector of `a`:

- `""` gives the link text
- `"@href"` gives the link URL, converted to an absolute URL

## 2. All links on a page

Save as `configs/all_links.json`:

```json
{
  "item": "a",
  "fields": {
    "title": "",
    "url": "@href"
  }
}
```

Run it against the quotes demo site and write JSON (the `.json` extension selects JSON output):

```bash
cd scraper
python static_list_scraper.py https://quotes.toscrape.com/ -c configs/all_links.json -o links.json
```

Real result from this run:

```
INFO Wrote 55 rows to links.json
```

The first entries of `links.json`:

```json
[
  {
    "title": "Quotes to Scrape",
    "url": "https://quotes.toscrape.com/"
  },
  {
    "title": "Login",
    "url": "https://quotes.toscrape.com/login"
  },
  {
    "title": "(about)",
    "url": "https://quotes.toscrape.com/author/Albert-Einstein"
  }
]
```

Output is written with `ensure_ascii=False`, so non-English text stays readable.

## 3. Only some links

An unfiltered `a` is noisy. Narrow the `item` selector to the part of the page you care about. To get only the author profile links from the quote list:

```json
{
  "item": "div.quote span a",
  "fields": {
    "label": "",
    "url": "@href"
  }
}
```

```bash
python static_list_scraper.py https://quotes.toscrape.com/ -c configs/author_links.json -o authors.json
```

This returned 10 rows on page 1, each with `"label": "(about)"` and a URL such as `https://quotes.toscrape.com/author/Albert-Einstein`. The link text is just "(about)". If you want the author name, take it from `small.author` in the same quote block, using the quote as the item:

```json
{
  "item": "div.quote",
  "fields": {
    "author": "small.author",
    "author_url": "span a@href"
  }
}
```

## 4. Remove duplicates afterwards

The script does not deduplicate. Navigation links often repeat. A short post-processing step:

```python
import json
rows = json.load(open("links.json", encoding="utf-8"))
seen, unique = set(), []
for r in rows:
    if r["url"] not in seen:
        seen.add(r["url"])
        unique.append(r)
json.dump(unique, open("links_unique.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(rows), "->", len(unique))
```

## 5. Other attributes

Any attribute works, not only `href`. Only `href` and `src` are made absolute; other attributes come back as written. Examples: `img@src`, `img@alt`, `meta.keywords@content`, `a@title`.

## Common errors

- **A column is empty**: the attribute does not exist on that element. For example `a@title` is empty on links without a title attribute.
- **Relative URLs in a custom attribute**: only `href` and `src` are joined to the page URL. Fix other attributes yourself afterwards with `urllib.parse.urljoin`.
- **Zero rows**: the `item` selector matched nothing. Test it in the browser console with `document.querySelectorAll("div.quote span a").length`.
- **Links built by JavaScript are missing**: the scraper downloads HTML only and does not run scripts.
- **`mailto:` and `javascript:` entries**: filter them in the post-processing step.

---
Need the full kit (15 blocks: Discord bots, paginated & Selenium scrapers, RSS collector, pandas cleaner, OpenAPI + Postman)? **Automation Script Pack — $39:** https://raxsoft.gumroad.com/l/fkits
