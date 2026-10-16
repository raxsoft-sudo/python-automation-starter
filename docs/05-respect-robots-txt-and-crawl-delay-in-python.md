# How to respect robots.txt and Crawl-delay in Python

A polite scraper checks `robots.txt` before each host, identifies itself, and slows down. The shared module `scraper/common.py` already does this. This guide shows what it does, how to test it, and how to reuse the same idea in your own code.

## What robots.txt is, and is not

`robots.txt` is a plain-text file at the root of a site (`https://example.com/robots.txt`) listing which paths automated clients should avoid, and sometimes a `Crawl-delay`. It is a convention, not access control and not a legal permission. Terms of service, copyright and privacy law still apply. If a site says no, the right move is to skip it.

## What this repo does

`RobotsChecker` in `common.py`:

1. Fetches `robots.txt` once per host, using your own User-Agent, and caches it.
2. On HTTP 200 it parses the rules.
3. On a 4xx (for example 404) it treats everything as allowed, which is the usual reading.
4. On a 5xx or a network failure it assumes everything is **disallowed**, to be conservative.
5. `PoliteFetcher.get` returns `None` and logs `Blocked by robots.txt, skipping` for disallowed URLs.
6. If the file has a `Crawl-delay` larger than your `--delay`, the delay is raised to match.

Both `books.toscrape.com/robots.txt` and `quotes.toscrape.com/robots.txt` return 404 (checked), so everything is allowed on those practice sites.

## Test the parser offline

You can see exactly how Python interprets a robots.txt without any network:

```python
from urllib import robotparser

rp = robotparser.RobotFileParser()
rp.parse("""User-agent: *
Crawl-delay: 5
Disallow: /private/""".splitlines())

print(rp.can_fetch("MyBot", "https://x.test/private/a"))  # False
print(rp.can_fetch("MyBot", "https://x.test/ok"))         # True
print(rp.crawl_delay("MyBot"))                            # 5
```

Output when run: `False True 5`.

## Set your identity and delay

Replace the placeholder User-Agent so site owners can contact you:

```bash
cd scraper
python static_list_scraper.py https://quotes.toscrape.com/ -c configs/quotes.json -o quotes.csv \
  --user-agent "MyResearchBot/1.0 (contact: me@example.org)" --delay 2
```

A 1-second default delay is a minimum, not a goal. For anything bigger than a few pages, use 2 to 5 seconds, and scrape at quiet hours if you can.

## Reuse in your own script

```python
import sys
sys.path.insert(0, "scraper")
from common import PoliteFetcher

fetcher = PoliteFetcher(user_agent="MyBot/1.0 (contact: me@example.org)", delay=2)
resp = fetcher.get("https://quotes.toscrape.com/page/2/")
if resp is None:
    print("blocked or failed")
else:
    print(resp.status_code, len(resp.text))
```

## What not to do

- Do not use `--ignore-robots` to get around a block. The flag exists for your own sites and test servers.
- Do not rotate User-Agents or IPs to hide your scraper.
- Do not hit a single host with parallel requests unless the owner agrees.
- Prefer an official API or data export when one exists.

## Common errors

- **`Blocked by robots.txt, skipping: <url>`**: expected behavior. Open `https://host/robots.txt` in your browser to see which rule applies.
- **`Could not fetch .../robots.txt (...); assuming disallowed`**: network trouble or a firewall. Fix connectivity; the scraper deliberately refuses to continue blind.
- **Everything blocked on a site that looks fine**: its robots.txt returned a 5xx error. Retry later.
- **Rules differ by bot name**: a `User-agent: MyBot` section applies only if your User-Agent string starts with that name. Otherwise the `*` section applies.
- **Crawl-delay ignored in your own code**: `urllib.robotparser` only reports it; you must sleep yourself (the repo's fetcher does).

---
Need the full kit (15 blocks: Discord bots, paginated & Selenium scrapers, RSS collector, pandas cleaner, OpenAPI + Postman)? **Automation Script Pack — $39:** https://raxsoft.gumroad.com/l/fkits
