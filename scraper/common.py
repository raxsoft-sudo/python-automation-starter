"""Shared helpers for the scraper modules: robots.txt, rate limiting, retries, output."""
from __future__ import annotations

import csv
import json
import logging
import random
import time
from pathlib import Path
from typing import Iterable
from urllib import robotparser
from urllib.parse import urlparse

import requests

DEFAULT_UA = "ScraperPack/1.0 (+https://example.com/bot-info; contact: you@example.com)"
log = logging.getLogger("scraper")


def setup_logging(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


class RobotsChecker:
    """Caches one parsed robots.txt per host. Fetched with our own User-Agent."""

    def __init__(self, user_agent: str, timeout: float = 15, enabled: bool = True):
        self.user_agent = user_agent
        self.timeout = timeout
        self.enabled = enabled
        self._cache: dict[str, robotparser.RobotFileParser] = {}

    def _load(self, base: str) -> robotparser.RobotFileParser:
        rp = robotparser.RobotFileParser()
        robots_url = f"{base}/robots.txt"
        try:
            resp = requests.get(robots_url, headers={"User-Agent": self.user_agent}, timeout=self.timeout)
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
            elif 400 <= resp.status_code < 500:
                rp.parse([])  # no robots.txt => everything allowed
            else:
                rp.parse(["User-agent: *", "Disallow: /"])  # server trouble => be conservative
        except requests.RequestException as exc:
            log.warning("Could not fetch %s (%s); assuming disallowed", robots_url, exc)
            rp.parse(["User-agent: *", "Disallow: /"])
        return rp

    def allowed(self, url: str) -> bool:
        if not self.enabled:
            return True
        parts = urlparse(url)
        base = f"{parts.scheme}://{parts.netloc}"
        if base not in self._cache:
            self._cache[base] = self._load(base)
        return self._cache[base].can_fetch(self.user_agent, url)

    def crawl_delay(self, url: str) -> float | None:
        parts = urlparse(url)
        rp = self._cache.get(f"{parts.scheme}://{parts.netloc}")
        return rp.crawl_delay(self.user_agent) if rp else None


class RateLimiter:
    def __init__(self, delay: float):
        self.delay = max(0.0, delay)
        self._last = 0.0

    def wait(self) -> None:
        elapsed = time.monotonic() - self._last
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last = time.monotonic()


class PoliteFetcher:
    """requests-based GET with robots.txt, rate limit, retries and exponential backoff."""

    def __init__(
        self,
        user_agent: str = DEFAULT_UA,
        delay: float = 1.0,
        retries: int = 3,
        backoff: float = 2.0,
        timeout: float = 20,
        respect_robots: bool = True,
    ):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.robots = RobotsChecker(user_agent, timeout, respect_robots)
        self.limiter = RateLimiter(delay)
        self.retries = retries
        self.backoff = backoff
        self.timeout = timeout

    def get(self, url: str) -> requests.Response | None:
        """Return a successful Response or None (blocked by robots / failed after retries)."""
        if not self.robots.allowed(url):
            log.warning("Blocked by robots.txt, skipping: %s", url)
            return None
        crawl_delay = self.robots.crawl_delay(url)
        if crawl_delay and crawl_delay > self.limiter.delay:
            self.limiter.delay = float(crawl_delay)
        for attempt in range(1, self.retries + 2):
            self.limiter.wait()
            try:
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code in (429, 500, 502, 503, 504):
                    raise requests.HTTPError(f"HTTP {resp.status_code}", response=resp)
                resp.raise_for_status()
                return resp
            except requests.RequestException as exc:
                status = getattr(getattr(exc, "response", None), "status_code", None)
                if status and 400 <= status < 500 and status != 429:
                    log.error("GET %s failed: HTTP %s (not retrying)", url, status)
                    return None
                if attempt > self.retries:
                    log.error("GET %s failed after %d attempts: %s", url, attempt, exc)
                    return None
                wait = self.backoff ** attempt + random.uniform(0, 0.5)
                retry_after = getattr(getattr(exc, "response", None), "headers", {}).get("Retry-After")
                if retry_after and str(retry_after).isdigit():
                    wait = max(wait, float(retry_after))
                log.warning("GET %s failed (%s); retry %d/%d in %.1fs", url, exc, attempt, self.retries, wait)
                time.sleep(wait)
        return None


def write_output(rows: Iterable[dict], path: str | Path) -> int:
    """Write rows to .csv or .json (by extension). Returns number of rows."""
    rows = list(rows)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".json":
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        fields: list[str] = []
        for row in rows:
            for key in row:
                if key not in fields:
                    fields.append(key)
        with path.open("w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    log.info("Wrote %d rows to %s", len(rows), path)
    return len(rows)


def add_common_args(parser) -> None:
    """Flags shared by all HTTP scrapers."""
    parser.add_argument("--user-agent", default=DEFAULT_UA, help="User-Agent header (set your own contact info)")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds between requests (default 1.0)")
    parser.add_argument("--retries", type=int, default=3, help="Retries per request (default 3)")
    parser.add_argument("--backoff", type=float, default=2.0, help="Exponential backoff base (default 2.0)")
    parser.add_argument("--timeout", type=float, default=20, help="Request timeout seconds")
    parser.add_argument("--ignore-robots", action="store_true", help="Do NOT check robots.txt (not recommended)")
    parser.add_argument("-o", "--output", default="output.csv", help="Output file, .csv or .json (default output.csv)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Debug logging")
