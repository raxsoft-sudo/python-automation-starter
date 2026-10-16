# Retry and exponential backoff for flaky HTTP requests in Python

Networks fail and servers say "try later". A good scraper retries the right errors, waits longer each time, and gives up cleanly. `PoliteFetcher.get` in `scraper/common.py` does this. This guide explains its behavior and shows how to tune it.

## The rules in this repo

From `common.py`:

- Retried: HTTP 429, 500, 502, 503, 504, and connection or timeout errors.
- Not retried: other 4xx errors (404, 403, ...). They will not fix themselves.
- Total attempts: `--retries` + 1. The default is 3 retries, so 4 attempts.
- Wait before retry number *n*: `backoff ** n` seconds plus a random 0 to 0.5 seconds of jitter. With the default `--backoff 2.0` that is about 2, 4, 8 seconds.
- If the server sends a numeric `Retry-After` header, the wait is at least that long.
- Every attempt also respects `--delay` between requests.

## Tuning from the command line

```bash
cd scraper
python static_list_scraper.py https://quotes.toscrape.com/ -c configs/quotes.json -o quotes.csv \
  --retries 5 --backoff 2 --timeout 30 --delay 2
```

A larger `--timeout` helps slow servers. A larger `--backoff` makes each wait grow faster. More `--retries` is not always better: if a server is down, hammering it makes things worse.

## Watching it work

To see the retry path without bothering any real site, point the scraper at a local port where nothing is listening. `--ignore-robots` is used only because this is your own machine with no robots.txt:

```bash
python static_list_scraper.py http://127.0.0.1:9/ -c configs/quotes.json -o out.csv \
  --retries 2 --backoff 1.5 --ignore-robots --timeout 3
```

Real output from this run, shortened:

```
WARNING GET http://127.0.0.1:9/ failed (... connection refused ...); retry 1/2 in 1.8s
WARNING GET http://127.0.0.1:9/ failed (... connection refused ...); retry 2/2 in 2.5s
ERROR GET http://127.0.0.1:9/ failed after 3 attempts: ...
```

The waits are 1.5 plus jitter, then 2.25 plus jitter, matching `backoff ** attempt`. The script exits with code 1 and writes no file.

A 4xx error is not retried:

```bash
python static_list_scraper.py https://quotes.toscrape.com/nope -c configs/quotes.json -o out.csv
```

```
ERROR GET https://quotes.toscrape.com/nope failed: HTTP 404 (not retrying)
```

## Why backoff and jitter

Waiting the same fixed time makes all clients retry at the same moment. Exponential growth gives a struggling server room to recover, and random jitter spreads clients out. A cap on retries prevents infinite loops.

## The same pattern in your own code

```python
import random
import time

import requests

RETRY_STATUS = {429, 500, 502, 503, 504}

def get_with_retry(url, retries=3, backoff=2.0, timeout=20):
    for attempt in range(1, retries + 2):
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code in RETRY_STATUS:
                raise requests.HTTPError(f"HTTP {r.status_code}", response=r)
            r.raise_for_status()
            return r
        except requests.RequestException as exc:
            status = getattr(exc.response, "status_code", None)
            if status and 400 <= status < 500 and status != 429:
                return None                      # permanent error
            if attempt > retries:
                return None                      # out of attempts
            wait = backoff ** attempt + random.uniform(0, 0.5)
            ra = getattr(exc.response, "headers", {}).get("Retry-After")
            if ra and ra.isdigit():
                wait = max(wait, float(ra))
            time.sleep(wait)
```

Always pass `timeout`; `requests` has no default and can hang forever.

## Common errors

- **Script seems frozen**: it is sleeping between retries. Run with `-v` for debug logs, or lower `--retries`.
- **Constant `HTTP 429`**: you are going too fast. Raise `--delay` instead of just adding retries.
- **`HTTP 403` right away**: not retried; the server refuses you. Check robots.txt and your User-Agent.
- **Exit code 1, no CSV**: all attempts failed. The output file is written only after a successful fetch.
- **Timeouts on every try**: the host may be blocking or down; test it in a browser.

---
Need the full kit (15 blocks: Discord bots, paginated & Selenium scrapers, RSS collector, pandas cleaner, OpenAPI + Postman)? **Automation Script Pack — $39:** https://raxsoft.gumroad.com/l/fkits
