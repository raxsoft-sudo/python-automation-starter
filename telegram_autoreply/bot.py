"""Telegram keyword auto-reply bot (python-telegram-bot v21).

Rules live in a YAML or JSON file (see rules.yaml). Use /reload to re-read them
without restarting (restricted to ADMIN_IDS if set).
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO
)
log = logging.getLogger("autoreply")


@dataclass
class Rule:
    pattern: re.Pattern
    reply: str


def load_rules(path: Path) -> list[Rule]:
    """Load rules from YAML/JSON. Each rule: keywords (list) or regex (str), reply (str)."""
    text = path.read_text(encoding="utf-8")
    data = json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)
    rules: list[Rule] = []
    for i, item in enumerate((data or {}).get("rules", [])):
        reply = item.get("reply")
        if not reply:
            log.warning("Rule #%d has no reply, skipped", i)
            continue
        if item.get("regex"):
            pattern = re.compile(item["regex"], re.IGNORECASE)
        elif item.get("keywords"):
            words = "|".join(re.escape(str(k)) for k in item["keywords"])
            pattern = re.compile(rf"(?<!\w)(?:{words})(?!\w)", re.IGNORECASE)
        else:
            log.warning("Rule #%d needs 'keywords' or 'regex', skipped", i)
            continue
        rules.append(Rule(pattern, str(reply)))
    return rules


def admin_ids() -> set[int]:
    raw = os.getenv("ADMIN_IDS", "")
    return {int(x) for x in raw.split(",") if x.strip().isdigit()}


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if not msg or not msg.text:
        return
    for rule in context.bot_data["rules"]:
        if rule.pattern.search(msg.text):
            await msg.reply_text(rule.reply)
            return  # first matching rule wins


async def cmd_reload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    admins = admin_ids()
    user = update.effective_user
    if admins and (not user or user.id not in admins):
        await update.effective_message.reply_text("Not allowed.")
        return
    try:
        context.bot_data["rules"] = load_rules(context.bot_data["rules_path"])
    except Exception as exc:  # noqa: BLE001 - report any parse problem to the admin
        await update.effective_message.reply_text(f"Reload failed: {exc}")
        return
    await update.effective_message.reply_text(
        f"Reloaded {len(context.bot_data['rules'])} rules."
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text("Hi! Send me a message and I'll reply if I know it.")


def main() -> None:
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN in .env (see .env.example).")
    rules_path = Path(os.getenv("RULES_FILE", "rules.yaml"))
    app = Application.builder().token(token).build()
    app.bot_data["rules_path"] = rules_path
    app.bot_data["rules"] = load_rules(rules_path)
    log.info("Loaded %d rules from %s", len(app.bot_data["rules"]), rules_path)
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("reload", cmd_reload))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
