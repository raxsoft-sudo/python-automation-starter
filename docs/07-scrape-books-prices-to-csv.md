# Scrape books.toscrape.com prices to CSV (and fix the "Â£" symbol)

`books.toscrape.com` is a public practice bookshop. This guide scrapes titles, prices, ratings and stock into a CSV, scrapes several pages, and fixes an encoding problem you will meet: prices coming out as `Â£51.77`.

## 1. Config

Save as `scraper/configs/books_full.json`:

```json
{
  "item": "article.product_pod",
  "fields": {
    "title": "h3 a@title",
    "price": "p.price_color",
    "rating": "p.star-rating@class",
    "in_stock": "p.availability",
    "url": "h3 a@href",
    "image": "img@src"
  }
}
```

The `rating` field uses `@class`. When an attribute is a list (class is), the scraper joins it with spaces, giving `star-rating One`.

## 2. Run one page

```bash
cd scraper
python static_list_scraper.py https://books.toscrape.com/catalogue/page-2.html -c configs/books_full.json -o books_p2.csv
```

Real result: `INFO Wrote 20 rows to books_p2.csv`. First rows:

```
title,price,rating,in_stock,url,image
In Her Wake,Â£12.84,star-rating One,In stock,https://books.toscrape.com/catalogue/in-her-wake_980/index.html,https://books.toscrape.com/media/cache/5d/72/5d72709c6a7a9584a4d1cf07648bfce1.jpg
How Music Works,Â£37.32,star-rating Two,In stock,https://books.toscrape.com/catalogue/how-music-works_979/index.html,https://books.toscrape.com/media/cache/5c/c8/5cc8e107246cb478960d4f0aba1e1c8e.jpg
```

## 3. Why "Â£"?

The server sends UTF-8 HTML but does not declare the charset in its HTTP header. The `requests` library then guesses ISO-8859-1 for `text/html`, so the two UTF-8 bytes of `£` show up as `Â£`. Plain ASCII text is unaffected; only non-ASCII characters are damaged.

The fix that needs no code change is to repair the column after scraping:

```python
import pandas as pd

df = pd.read_csv("books_p2.csv", encoding="utf-8-sig")
df["price"] = (
    df["price"].str.encode("latin-1").str.decode("utf-8")  # Â£12.84 -> £12.84
      .str.replace("£", "", regex=False)
      .astype(float)
)
print(df[["title", "price"]].head(3))
```

Prices come out as `12.84`, `37.32`, `30.52`. Apply the same encode/decode trick to `title` if you see damaged characters there. If you are willing to edit `common.py`, setting `resp.encoding = "utf-8"` before `resp.text` is read fixes it at the source, but that is a change to the repo code, not something the CLI flags offer.

## 4. Tidy rating and stock

```python
df["rating"] = df["rating"].str.replace("star-rating ", "", regex=False).map(
    {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5})
df["in_stock"] = df["in_stock"].str.contains("In stock")
```

## 5. Several pages

Catalogue pages are `catalogue/page-1.html` to `page-50.html`. Run the scraper once per page and keep a pause between runs, because the delay only applies within a single run:

```bash
for i in 1 2 3; do
  python static_list_scraper.py "https://books.toscrape.com/catalogue/page-$i.html" \
    -c configs/books_full.json -o "books_p$i.csv"
  sleep 2
done
```

Combine:

```python
import glob
import pandas as pd

df = pd.concat([pd.read_csv(f, encoding="utf-8-sig") for f in sorted(glob.glob("books_p*.csv"))],
               ignore_index=True)
df = df.drop_duplicates("url")
print(len(df))   # 60 for three pages of 20
```

## Common errors

- **`Â£` in prices**: encoding issue, see step 3.
- **`No items matched selector 'article.product_pod'`**: the page URL is wrong, or you ran the books config on another site (for example quotes.toscrape.com).
- **404 for `page-1.html` at the site root**: listing pages live under `/catalogue/`; only the homepage sits at `/`.
- **Price will not convert to float**: the column still has `£` or stray spaces; strip first.
- **Image URLs**: `img@src` is made absolute automatically, so you should see full `https://books.toscrape.com/media/...` links.

---
Need the full kit (15 blocks: Discord bots, paginated & Selenium scrapers, RSS collector, pandas cleaner, OpenAPI + Postman)? **Automation Script Pack — $39:** https://raxsoft.gumroad.com/l/fkits
