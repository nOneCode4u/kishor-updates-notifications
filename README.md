# Kishor Magazine Updates Notifications

**GitHub Actions bot** that sends beautiful Telegram notifications every time a new Kishor magazine issue is published on [ebalbharati.in](https://kishor.ebalbharati.in/Archives/).

### Features
- Detects new PDFs using direct file checks (robust against website changes)
- Beautiful formatted notifications with Marathi + English titles, size and direct links
- Full public history in `updates-history.md`
- Auto-pauses on any error and sends full details to Telegram

### How to use this repo on your own GitHub account (fork & run)

1. **Fork** this repository (top-right button → Fork)
2. Go to your forked repo → **Settings → Secrets and variables → Actions → New repository secret**
   - `TELEGRAM_BOT_TOKEN` → your bot token from @BotFather
   - `TELEGRAM_CHAT_ID` → your numeric chat ID (send any message to your bot, then forward to @userinfobot)
3. Edit `last_detected.txt` → set it to the last file you already have (example: `2026_02.pdf`)
4. Edit `kishor_status.txt` → make sure the first word is `active`
5. The workflow will start automatically.

**Manual resume after error**  
Edit `kishor_status.txt` → change first word to `active` → commit.

**Debug / Logs**  
Go to **Actions** tab → click any “Kishor Magazine Updates” run → “check-updates” job.

**History**  
See `updates-history.md` (auto-updated on every successful notification).
