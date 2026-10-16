# Deploy the Telegram auto-reply bot on a cheap VPS with systemd

This guide runs `telegram_autoreply/bot.py` 24/7 on a small Linux server (Ubuntu or Debian; 512 MB of RAM is plenty) and restarts it after crashes and reboots. The bot uses long polling, so no domain, TLS certificate or open inbound port is needed.

Note: the bot's rule logic was tested locally, but these server commands were not run while writing this guide. Follow them on a fresh server and check each step.

## 1. Prepare the server

Log in over SSH, install Python, and create a dedicated user without sudo rights:

```bash
sudo apt update && sudo apt install -y python3 python3-venv git
sudo adduser --system --group --home /opt/tgbot tgbot
```

## 2. Copy the code

```bash
sudo -u tgbot -H bash -c '
  cd /opt/tgbot
  git clone <YOUR-REPO-URL> app
  cd app/telegram_autoreply
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
  cp .env.example .env
'
```

If you do not use git, copy the `telegram_autoreply/` folder with `scp -r` instead and fix ownership with `sudo chown -R tgbot:tgbot /opt/tgbot`.

## 3. Fill in `.env`

```bash
sudo -u tgbot nano /opt/tgbot/app/telegram_autoreply/.env
sudo chmod 600 /opt/tgbot/app/telegram_autoreply/.env
```

```
TELEGRAM_BOT_TOKEN=123456:your-token
RULES_FILE=rules.yaml
ADMIN_IDS=111111111
```

Put your own Telegram user ID in `ADMIN_IDS` so only you can run `/reload`.

## 4. Test by hand

```bash
cd /opt/tgbot/app/telegram_autoreply
sudo -u tgbot .venv/bin/python bot.py
```

Look for `Loaded N rules from rules.yaml`, message the bot, then stop it with Ctrl+C.

## 5. Create the service

Create `/etc/systemd/system/tgbot.service`:

```ini
[Unit]
Description=Telegram auto-reply bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=tgbot
Group=tgbot
WorkingDirectory=/opt/tgbot/app/telegram_autoreply
ExecStart=/opt/tgbot/app/telegram_autoreply/.venv/bin/python bot.py
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

`WorkingDirectory` matters: `bot.py` looks for `.env` and `rules.yaml` relative to the current folder.

## 6. Start it

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now tgbot
sudo systemctl status tgbot
```

Status should say `active (running)`.

## 7. Logs, updates, rule changes

```bash
journalctl -u tgbot -f                  # live logs
journalctl -u tgbot --since "1 hour ago"
```

- Edit rules: change `rules.yaml`, then send `/reload` to the bot. No restart needed.
- Update code: `cd /opt/tgbot/app && sudo -u tgbot git pull`, then `sudo systemctl restart tgbot`.
- Stop it: `sudo systemctl stop tgbot`. Do not start at boot: `sudo systemctl disable tgbot`.

## 8. Basic hygiene

- Use SSH keys only and install security updates regularly.
- Never commit `.env`. The repo's `.gitignore` already lists it.
- If the token ever leaks, send `/revoke` to @BotFather and update `.env`.
- Run only one copy of the bot per token.

## Common errors

- **`status=200/CHDIR`**: `WorkingDirectory` does not exist or `tgbot` cannot read it.
- **`status=203/EXEC`**: the `ExecStart` path is wrong or the venv was not created.
- **`Set TELEGRAM_BOT_TOKEN in .env`** in the logs: `.env` is missing from the working directory or unreadable by `tgbot`.
- **`Conflict: terminated by other getUpdates request`**: the bot is also running somewhere else (your laptop). Stop that copy.
- **Service restarts repeatedly**: read `journalctl -u tgbot -n 50`. A YAML error in `rules.yaml` at startup stops the bot; fix the file and restart.
- **`ModuleNotFoundError`**: packages were installed outside the venv. Use `.venv/bin/pip`.

---
Need the full kit (15 blocks: Discord bots, paginated & Selenium scrapers, RSS collector, pandas cleaner, OpenAPI + Postman)? **Automation Script Pack — $39:** https://raxsoft.gumroad.com/l/fkits
