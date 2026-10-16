# Telegram Auto-Reply Bot

Replies to messages that match keywords or regexes defined in `rules.yaml` (or a `.json` file).

## Setup
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env     # then fill in TELEGRAM_BOT_TOKEN (get one from @BotFather)
python bot.py
```

## Rules
```yaml
rules:
  - keywords: [hello, hi]      # whole-word, case-insensitive
    reply: "Hello!"
  - regex: "order\\s*#?\\d+"   # or a regular expression
    reply: "Looking up your order."
```
First matching rule wins. JSON format: `{"rules": [{"keywords": ["hi"], "reply": "Hello"}]}`.

## Commands
- `/start` greeting
- `/reload` re-read the rules file without restarting (limited to `ADMIN_IDS` if set)

In groups, disable privacy mode via @BotFather (`/setprivacy`) so the bot can see messages.
