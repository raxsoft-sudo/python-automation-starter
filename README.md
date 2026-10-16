# Python Automation Starter

Two small, working building blocks for automation jobs:

- **`telegram_autoreply/`** — Telegram bot that answers by keyword rules from a YAML file (`/reload` without restart). python-telegram-bot v21.
- **`scraper/`** — polite list scraper: robots.txt check, rate limiting, retries with backoff, CSV/JSON export, CSS selectors in a JSON config.

## Quickstart

### Scraper
```bash
cd scraper
pip install -r requirements.txt
python static_list_scraper.py https://quotes.toscrape.com/ -c configs/quotes.json -o quotes.csv
```
Set a real `--user-agent` with your contact info, and only scrape sites whose terms allow it. Run with `-h` for all options.

Config format:
```json
{ "item": "div.quote",
  "fields": { "text": "span.text", "author": "small.author", "author_url": "span a@href" } }
```

### Telegram auto-reply bot
```bash
cd telegram_autoreply
pip install -r requirements.txt
cp .env.example .env      # put your BotFather token here, never commit .env
python bot.py
```
Edit `rules.yaml` to change replies, then send `/reload` to the bot.

## Don't want to run it yourself?

The same CSS-selector extraction is available as a hosted API (free tier: 100 requests/month):
**Scrape to JSON on RapidAPI — https://rapidapi.com/%EA%B0%95%EC%A0%95%EC%8B%9D/api/scrape-to-json1**

## Want the full kit?

This repo is 2 of 15 blocks. The **Automation Script Pack** adds:

- Telegram group moderator, Discord auto-reply and moderation bots (discord.js v14), Telegram → Discord bridge
- Paginated scraper, Selenium headless scraper, RSS collector, pandas data cleaner
- OpenAPI 3.1 spec + Postman collection with tests

👉 **$39 — https://raxsoft.gumroad.com/l/fkits**

Need something built for your stack? Open an issue or email raxsoft@gmail.com.

## License
MIT for the code in this repository (see `LICENSE`).
