import requests
import os
import subprocess
import traceback
import datetime

# Human-made, clean constants
BASE_URL = "https://kishor.ebalbharati.in/Archives/include/pdf/"
STATUS_FILE = "kishor_status.txt"
LAST_DETECTED_FILE = "last_detected.txt"
HISTORY_FILE = "updates-history.md"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; KishorUpdatesBot/1.0; +https://github.com/kishor-updates-notifications)"
}

def send_telegram(message: str):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise Exception("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID secret")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        resp = requests.post(url, json=data, timeout=15)
        print(f"[DEBUG] Telegram API status: {resp.status_code}")
        print(f"[DEBUG] Telegram response: {resp.text[:800]}...")
        resp.raise_for_status()
        json_resp = resp.json()
        if not json_resp.get("ok"):
            raise Exception(f"Telegram API error: {json_resp.get('description')}")
        print("[DEBUG] Telegram message sent successfully.")
    except Exception as e:
        print(f"[DEBUG] Telegram send FAILED: {e}")
        raise

def git_commit_and_push(commit_message: str, files: list):
    """Commit and push only changed files."""
    subprocess.run(["git", "config", "--global", "user.name", "Kishor Updates Bot"], check=True)
    subprocess.run(["git", "config", "--global", "user.email", "kishor-bot@github.com"], check=True)
    for f in files:
        subprocess.run(["git", "add", f], check=True)
    subprocess.run(["git", "commit", "-m", commit_message], check=True)
    subprocess.run(["git", "push"], check=True)

def get_ist_now():
    """Return current IST datetime (timezone-aware)."""
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    ist_now = utc_now + datetime.timedelta(hours=5, minutes=30)
    return ist_now

def main():
    try:
        # === 1. Check status file ===
        if not os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "w", encoding="utf-8") as f:
                f.write("active\n# Edit to 'paused' or 'active'.")
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
        status = content.splitlines()[0].strip().lower().split()[0] if content else ""
        print(f"[DEBUG] Status file first word = '{status}'")
        if status != "active":
            print("[DEBUG] Workflow is paused. No detection run.")
            return

        # === 2. Read last detected ===
        with open(LAST_DETECTED_FILE, "r", encoding="utf-8") as f:
            last_detected = f.read().strip()
        print(f"[DEBUG] Last detected file: {last_detected}")

        # Month names
        eng_months = ["", "January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
        mar_months = ["", "जानेवारी", "फेब्रुवारी", "मार्च", "एप्रिल", "मे", "जून",
                      "जुलै", "ऑगस्ट", "सप्टेंबर", "ऑक्टोबर", "नोव्हेंबर", "डिसेंबर"]
        devanagari_digits = str.maketrans("0123456789", "०१२३४५६७८९")

        ist_now = get_ist_now()
        current_year = ist_now.year
        current_mon = ist_now.month
        print(f"[DEBUG] Current IST: {ist_now.strftime('%Y-%m-%d %H:%M:%S')}")

        # Detect new issues
        new_issues = []
        last_base = last_detected[:-4]
        last_year = int(last_base[:4])
        last_mon = int(last_base[5:])

        for year in range(last_year, current_year + 2):
            start_mon = last_mon + 1 if year == last_year else 1
            for mon in range(start_mon, 13):
                if (year == current_year and mon > current_mon + 3) or (year > current_year and mon > 3):
                    break
                fname = f"{year:04d}_{mon:02d}.pdf"
                url = BASE_URL + fname
                print(f"[DEBUG] Checking {fname} → {url}")

                resp = requests.head(url, headers=HEADERS, timeout=12, allow_redirects=True)

                if resp.status_code == 200:
                    size_bytes = int(resp.headers.get("content-length", 0))
                    size_mb = size_bytes / (1024 * 1024)
                    new_issues.append((fname, round(size_mb, 2), url))
                    print(f"[DEBUG] ✓ Found new issue: {fname} ({size_mb:.2f} MB)")
                else:
                    print(f"[DEBUG] No file (status {resp.status_code})")

        if new_issues:
            new_last = new_issues[-1][0]
            num = len(new_issues)
            date_str = ist_now.strftime("%d/%m/%Y")
            time_str = ist_now.strftime("%H:%M:%S")

            header = f"🤖 <b>Kishor Updates Notifications</b>\n\n📖 {num} New Magazine Issues Detected\n(after last detected <b>{last_detected}</b>)\n\n📆 <b>Date:</b> {date_str}\n🕖 <b>Time:</b> {time_str}\n\n"

            body = ""
            for fname, size, url in new_issues:
                y_str, m_str = fname[:-4].split("_")
                year = int(y_str)
                mon_idx = int(m_str)
                eng = eng_months[mon_idx]
                mar = mar_months[mon_idx]
                year_dev = str(year).translate(devanagari_digits)
                title = f"`किशोर {mar} {year_dev} - Kishor {eng} {year}.pdf`"
                body += f"{title} <b>({fname} • {size:.2f} MB)</b>\n{url}\n\n"

            full_message = header + body
            send_telegram(full_message)

            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(f"\n## {date_str} {time_str} - {num} New Magazine Issues Detected (after {last_detected})\n\n")
                f.write(body)
                f.write("\n---\n")

            with open(LAST_DETECTED_FILE, "w", encoding="utf-8") as f:
                f.write(new_last)

            git_commit_and_push(
                f"Update last detected to {new_last} — {num} new issues + history",
                files=[LAST_DETECTED_FILE, HISTORY_FILE]
            )
            print(f"[DEBUG] Success: {num} new issues notified.")
        else:
            print("[DEBUG] No new issues found this run.")

    except Exception as e:
        # Full traceback for Telegram only (as you requested)
        tb = traceback.format_exc()
        error_msg = f"""🤖 <b>Kishor Updates Notifications</b>

❌ <b>Error</b>: Detection Failed
⚠️ <b>Reason</b>: {str(e)}
🧾 <b>Error Details</b>: {tb}

⏸ Workflow <b>paused</b>

🛠 Change status in <code>kishor_status.txt</code> Manually"""

        try:
            send_telegram(error_msg)
        except:
            pass

        # NO GitHub Issue creation (removed completely as requested)
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            f.write("paused\n# Edit to 'active' and commit to resume.")
        git_commit_and_push("❌ Paused due to error", files=[STATUS_FILE])
        print("[DEBUG] Workflow paused due to error.")
        return

if __name__ == "__main__":
    main()
