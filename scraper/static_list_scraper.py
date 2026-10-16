"""Static list scraper: extract repeated items from one page using CSS selectors from a config.

Example:
    python static_list_scraper.py https://quotes.toscrape.com/ -c configs/quotes.json -o quotes.csv
"""
from __future__ import annotations

import argparse
import json
import sys
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from common import PoliteFetcher, add_common_args, log, setup_logging, write_output


def extract_items(html: str, base_url: str, config: dict) -> list[dict]:
    """config = {"item": "div.quote", "fields": {"text": "span.text", "link": "a@href"}}
    A selector may end with `@attr` to read an attribute instead of text.
    """
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for node in soup.select(config["item"]):
        row = {}
        for name, selector in config["fields"].items():
            sel, _, attr = selector.partition("@")
            el = node.select_one(sel.strip()) if sel.strip() else node
            if el is None:
                row[name] = ""
            elif attr:
                value = el.get(attr.strip(), "")
                if isinstance(value, list):
                    value = " ".join(value)
                row[name] = urljoin(base_url, value) if attr.strip() in ("href", "src") else value
            else:
                row[name] = " ".join(el.get_text(" ", strip=True).split())
        rows.append(row)
    return rows


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("url", help="Page URL")
    p.add_argument("-c", "--config", required=True, help="JSON config with CSS selectors")
    add_common_args(p)
    args = p.parse_args(argv)
    setup_logging(args.verbose)

    try:
        with open(args.config, encoding="utf-8") as fh:
            config = json.load(fh)
        config["item"], config["fields"]
    except (OSError, ValueError, KeyError) as exc:
        log.error("Bad config %s: %s", args.config, exc)
        return 2

    fetcher = PoliteFetcher(args.user_agent, args.delay, args.retries, args.backoff, args.timeout, not args.ignore_robots)
    resp = fetcher.get(args.url)
    if resp is None:
        return 1
    rows = extract_items(resp.text, resp.url, config)
    if not rows:
        log.warning("No items matched selector %r", config["item"])
    write_output(rows, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
