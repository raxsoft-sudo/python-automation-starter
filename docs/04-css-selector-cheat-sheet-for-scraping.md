# CSS selector cheat sheet for web scraping with BeautifulSoup

`static_list_scraper.py` uses BeautifulSoup's `select` and `select_one`, so everything here works in its JSON configs and in your own Python code. The examples use the structure of quotes.toscrape.com, where each quote looks like this:

```html
<div class="quote">
  <span class="text">“...”</span>
  <span>by <small class="author">Albert Einstein</small>
    <a href="/author/Albert-Einstein">(about)</a></span>
  <div class="tags">Tags: <a class="tag" href="/tag/change/page/1/">change</a> ...</div>
</div>
```

## Basic selectors

| Selector | Matches | Example |
|---|---|---|
| `tag` | all elements of that tag | `a` |
| `.class` | elements with that class | `.quote` |
| `#id` | the element with that id | `#header` |
| `tag.class` | tag with class | `div.quote` |
| `.a.b` | has both classes | `p.star-rating.Three` |

## Relationships

| Selector | Meaning | Example |
|---|---|---|
| `A B` | B anywhere inside A | `div.quote span.text` |
| `A > B` | B directly inside A | `div.quote > span.text` |
| `A + B` | B immediately after A | `h3 + p` |
| `A ~ B` | any B after A, same parent | `h3 ~ p` |
| `A, B` | either A or B | `h1, h2` |

## Attributes

| Selector | Meaning |
|---|---|
| `[href]` | has an href |
| `a[href^="/author"]` | href starts with |
| `a[href$=".pdf"]` | href ends with |
| `a[href*="tag"]` | href contains |
| `meta[name="keywords"]` | exact attribute value |

## Position and text

| Selector | Meaning |
|---|---|
| `li:nth-of-type(2)` | the second `li` among siblings of its type |
| `li:first-of-type`, `li:last-of-type` | first or last of its type |
| `li:nth-of-type(odd)` | odd positions |
| `a:-soup-contains("Next")` | link whose text contains "Next" (soupsieve syntax; the old `:contains()` is deprecated) |

## The scraper's own `@attr` extension

This is not CSS; it is the config syntax in this repo. A field selector can end with `@attribute`:

| Field value | Result |
|---|---|
| `"span.text"` | text of the first match |
| `"small.author"` | text of the first match |
| `"span a@href"` | `href` of the first match, made absolute |
| `"h3 a@title"` | `title` attribute of the link |
| `"img@src"` | image URL, made absolute |
| `"@href"` | `href` of the item itself |
| `""` | text of the item itself |

Remember that a field selector returns only the **first** match inside the item. The `item` selector returns **all** matches.

## Real examples, verified

Using `a.tag` as a field on quotes.toscrape.com page 2 gives only the first tag of each quote (`friends`, `courage`, ...). To get all tags in one cell, use the page's meta tag:

```json
{
  "item": "div.quote",
  "fields": {
    "text": "span.text",
    "author": "small.author",
    "tags": "meta.keywords@content"
  }
}
```

Real output row: `Marilyn Monroe`, tags `friends,heartbreak,inspirational,life,love,sisters`. Using `div.tags` instead gives the text `Tags: change deep-thoughts thinking world`, including the "Tags:" label.

## How to find a selector fast

1. Right-click the element in your browser, choose Inspect.
2. Right-click the highlighted node, Copy, Copy selector. Shorten it by hand; browser-generated selectors are usually too specific.
3. Test in the console: `document.querySelectorAll("div.quote").length`. It should equal the number of items you see.

## Common errors

- **Selector works in the browser but not in the scraper**: the browser ran JavaScript that built the elements. View the page source (Ctrl+U) and check the element is in the raw HTML.
- **Only one value where you expected many**: field selectors return the first match. Use the item selector, or a combined attribute like `meta.keywords@content`.
- **Class with special characters**: escape them, e.g. `.col-1\/2`.
- **`SelectorSyntaxError`** in your own code: unbalanced quotes or brackets in an attribute selector.
- **Space inside a class chain**: write `.a.b` for "both classes". `.a .b` means "b inside a".
- **An `@` inside the CSS itself**: the config splits at the first `@`, so avoid attribute selectors that contain `@` (such as an email in `a[href*="@"]`).

---
Need the full kit (15 blocks: Discord bots, paginated & Selenium scrapers, RSS collector, pandas cleaner, OpenAPI + Postman)? **Automation Script Pack — $39:** https://raxsoft.gumroad.com/l/fkits
