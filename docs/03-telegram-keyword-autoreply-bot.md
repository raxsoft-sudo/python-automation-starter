# Build a Telegram keyword auto-reply bot in 10 minutes (python-telegram-bot v21)

This guide sets up `telegram_autoreply/`, a small bot that answers messages when they contain keywords or match a regular expression. Rules live in a YAML file, and `/reload` re-reads them without restarting.

## 1. Create the bot token

In Telegram, open a chat with @BotFather, send `/newbot`, and follow the prompts. BotFather gives you a token. Treat it like a password: never commit it or paste it into a public place.

## 2. Install

```bash
cd telegram_autoreply
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # Windows: copy .env.example .env
```

The requirements are `python-telegram-bot>=21.0,<22`, `PyYAML` and `python-dotenv`.

## 3. Configure `.env`

```
TELEGRAM_BOT_TOKEN=123456:your-token-from-botfather
RULES_FILE=rules.yaml
ADMIN_IDS=
```

`ADMIN_IDS` is a comma-separated list of Telegram user IDs allowed to run `/reload`. If it is empty, anyone can. Set it before you share the bot.

## 4. Write rules

Open `rules.yaml`. Each rule has a `reply` and either `keywords` or `regex`:

```yaml
rules:
  - keywords: [refund, "money back"]
    reply: "Refunds take 5 business days."
  - keywords: [hello, hi, hey]
    reply: "Hello! How can I help you today?"
  - regex: 'order\s*#?\d+'
    reply: "Looking up your order."
```

How matching works, from the code in `bot.py`:

- Keywords match whole words, case-insensitive. `hi` matches "Hi there" but not "history".
- A multi-word keyword such as `money back` matches as a phrase.
- A regex is searched anywhere in the message, case-insensitive.
- **The first matching rule wins**, so put specific rules above general ones.
- A rule without a `reply`, or without `keywords` or `regex`, is skipped with a warning.

Single quotes around the regex avoid YAML escape problems. In double quotes you must write `"order\\s*#?\\d+"` (the shipped `rules.yaml` does this).

I checked these rules by loading them with the bot's own `load_rules` function and testing messages:

```
"Hi there"             -> Hello!
"this is a history"    -> (no reply)
"I want my MONEY BACK" -> Refunds take 5 business days.
"order #123"           -> Looking up your order.
"Order 55"             -> Looking up your order.
```

A JSON rules file works too (the file extension decides): `{"rules": [{"keywords": ["hi"], "reply": "Hello"}]}`.

## 5. Run

```bash
python bot.py
```

You should see a log line like `Loaded 4 rules from rules.yaml`. Message your bot in Telegram. The bot uses long polling, so it needs no public address or open port.

## 6. Change rules without restarting

Edit `rules.yaml`, then send `/reload` to the bot. It answers `Reloaded N rules.` or `Reload failed: ...` with the parse error, and keeps the old rules if the new file is broken. The `/start` command sends a short greeting.

## 7. Use it in a group

By default Telegram bots in groups may not see ordinary messages. Open @BotFather, send `/setprivacy`, pick your bot, and choose Disable. Then remove and re-add the bot to the group.

## Common errors

- **`Set TELEGRAM_BOT_TOKEN in .env`**: the `.env` file is missing, empty, or you started `python bot.py` from another folder. Run it from inside `telegram_autoreply/`.
- **`telegram.error.InvalidToken`**: the token is wrong or has extra spaces or quotes.
- **`telegram.error.Conflict: terminated by other getUpdates request`**: the same bot is running twice (another terminal, or a server). Stop the other one.
- **Bot ignores messages in a group**: privacy mode is still on (step 7).
- **`/reload` says `Not allowed.`**: your user ID is not in `ADMIN_IDS`.
- **A rule never fires**: an earlier rule matches first, or the keyword is only part of a longer word.

Note: the bot was not connected to the live Telegram service while writing this guide (that needs a real token); the rule-matching results above come from running `load_rules` locally.

---
Need the full kit (15 blocks: Discord bots, paginated & Selenium scrapers, RSS collector, pandas cleaner, OpenAPI + Postman)? **Automation Script Pack — $39:** https://raxsoft.gumroad.com/l/fkits
