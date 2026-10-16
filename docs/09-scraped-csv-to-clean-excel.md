# Turn a scraped CSV into a clean Excel file with pandas

Scraper CSVs open fine in code but often look rough in Excel: broken symbols, numbers stored as text, long raw URLs. This guide converts the `books.toscrape.com` output from [guide 07](07-scrape-books-prices-to-csv.md) into a tidy `.xlsx`.

## 1. Install

```bash
pip install pandas openpyxl
```

`openpyxl` is what pandas uses to write `.xlsx`.

## 2. Get a CSV

```bash
cd scraper
python static_list_scraper.py https://books.toscrape.com/catalogue/page-2.html -c configs/books_full.json -o books_p2.csv
```

(Config from guide 07.) The file is written as UTF-8 with a byte-order mark (`utf-8-sig`), which is why Excel opens it with correct accents when double-clicked. When reading it with pandas, pass `encoding="utf-8-sig"` so the BOM does not end up in the first column name.

## 3. The cleaning script

Save as `clean.py`:

```python
import pandas as pd

df = pd.read_csv("books_p2.csv", encoding="utf-8-sig")

# 1. Repair "Â£12.84" and convert to a real number
df["price"] = (
    df["price"].str.encode("latin-1").str.decode("utf-8")
      .str.replace("£", "", regex=False)
      .astype(float)
)

# 2. "star-rating Three" -> 3
df["rating"] = (
    df["rating"].str.replace("star-rating ", "", regex=False)
      .map({"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5})
)

# 3. Text to boolean
df["in_stock"] = df["in_stock"].str.contains("In stock")

# 4. Remove repeated rows and sort
df = df.drop_duplicates("url").sort_values("price")

# 5. Write Excel
df.to_excel("books.xlsx", index=False, sheet_name="books")
print(df[["title", "price", "rating", "in_stock"]].head(3).to_string())
```

Real output of this script on page 2 (the long title column is shortened here):

```
                                                         title  price  rating  in_stock
0                                                  In Her Wake  12.84       1      True
14                                              Sophie's World  15.94       5      True
10  The Four Agreements: A Practical Guide to Personal Freedom  17.66       5      True
```

`books.xlsx` was created. The left-hand numbers are the old row positions, which is normal after sorting.

## 4. Make it look right in Excel

Add column widths, a frozen header and a price number format with `openpyxl` after saving:

```python
from openpyxl import load_workbook

wb = load_workbook("books.xlsx")
ws = wb["books"]
ws.freeze_panes = "A2"
widths = {"A": 50, "B": 10, "C": 8, "D": 10, "E": 60, "F": 60}
for col, w in widths.items():
    ws.column_dimensions[col].width = w
for cell in ws["B"][1:]:
    cell.number_format = "0.00"
ws.auto_filter.ref = ws.dimensions
wb.save("books.xlsx")
```

The column letters follow the column order: title, price, rating, in_stock, url, image.

## 5. Multiple CSVs into one workbook

```python
import glob
import pandas as pd

with pd.ExcelWriter("all_books.xlsx") as xw:
    for f in sorted(glob.glob("books_p*.csv")):
        pd.read_csv(f, encoding="utf-8-sig").to_excel(xw, sheet_name=f[:-4], index=False)
```

Sheet names are limited to 31 characters.

## Common errors

- **`ModuleNotFoundError: No module named 'openpyxl'`**: run `pip install openpyxl`.
- **`UnicodeDecodeError` when reading the CSV**: add `encoding="utf-8-sig"`.
- **`ValueError: could not convert string to float`**: some price cells still hold `Â£` or spaces; clean them before `astype(float)`.
- **`PermissionError` on save**: the `.xlsx` is open in Excel. Close it first.
- **`AttributeError: Can only use .str accessor`**: the column is already numeric, usually because the cleaning step ran twice on the same DataFrame.
- **Long numbers or IDs show as `1E+15`**: write them as text with `df["id"] = df["id"].astype(str)` before exporting.

---
Need the full kit (15 blocks: Discord bots, paginated & Selenium scrapers, RSS collector, pandas cleaner, OpenAPI + Postman)? **Automation Script Pack — $39:** https://raxsoft.gumroad.com/l/fkits
