# Job Alert Bot 🚀

Hourly job alerts for **Senior PM roles** in Seattle — pulls from Indeed RSS, Greenhouse, and Lever. Runs free on GitHub Actions. Notifies via Telegram or Gmail.

---

## What it watches

| Layer | Tool | Cost |
|---|---|---|
| Scheduler | GitHub Actions cron | Free |
| Job sources | Indeed RSS + Greenhouse API + Lever API | Free |
| Dedup storage | `seen_jobs.json` committed to repo | Free |
| Notifications | Telegram bot or Gmail SMTP | Free |

25 companies monitored out of the box including Amazon, Microsoft, Google, Meta, Apple, Airbnb, Stripe, Netflix, Uber, Zillow, and more.

---

## Quick setup (10 minutes)

### Step 1 — Fork / clone this repo

```bash
git clone https://github.com/YOUR_USERNAME/job-alerts.git
cd job-alerts
```

### Step 2 — Edit `config.py`

Open `config.py` and customize:

- **TARGET_ROLES** — job titles you want alerts for
- **EXCLUDE_KEYWORDS** — noise to filter out
- **LOCATION** — your target city
- **COMPANIES** — add or remove companies
- **NOTIFY_TELEGRAM / NOTIFY_GMAIL** — pick your notification channel

### Step 3 — Set up Telegram bot (recommended)

1. Open Telegram → search `@BotFather` → `/newbot`
2. Follow prompts → copy the **bot token**
3. Start a chat with your new bot
4. Get your chat ID:
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
   Look for `"chat":{"id":XXXXXXX}` in the response

### Step 4 — Set up Gmail (optional, in addition to Telegram)

1. Go to your Google Account → Security → App Passwords
2. Create an App Password for "Mail" → copy the 16-char password
3. Set `GMAIL_TO` in `config.py` to your receiving email

### Step 5 — Add GitHub Secrets

Go to your repo → Settings → Secrets and variables → Actions → New repository secret

| Secret name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | From BotFather |
| `TELEGRAM_CHAT_ID` | Your chat ID number |
| `GMAIL_USER` | your.email@gmail.com |
| `GMAIL_APP_PASSWORD` | 16-char app password |
| `GMAIL_TO` | destination email (can be same) |

### Step 6 — Enable Actions and push

```bash
git add .
git commit -m "Initial job alert setup"
git push
```

Go to Actions tab → enable workflows if prompted → run manually to test.

---

## Add a new company

**If they use Greenhouse:**
```python
"Robinhood": {
    "type": "greenhouse",
    "slug": "robinhood",
},
```
Find the slug at: `https://boards.greenhouse.io/{slug}`

**If they use Lever:**
```python
"Waymo": {
    "type": "lever",
    "slug": "waymo",
},
```
Find the slug at: `https://jobs.lever.co/{slug}`

**If they use their own ATS (Indeed fallback):**
```python
"Twitch": {
    "type": "indeed",
    "query": "twitch+amazon+product+manager",
},
```

---

## Add a new job role

Open `config.py` → `TARGET_ROLES` → add any string that might appear in the job title:

```python
TARGET_ROLES = [
    "Senior Product Manager",
    "Technical Program Manager",   # ← add this
    "Senior TPM",                  # ← and this
    ...
]
```

---

## Run locally

```bash
pip install -r requirements.txt

# Set secrets as env vars
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."

python main.py
```

---

## File structure

```
job-alerts/
├── main.py            ← fetcher, dedup, notifications
├── config.py          ← all customization here
├── requirements.txt
├── seen_jobs.json     ← auto-updated by Actions each run
└── .github/
    └── workflows/
        └── job_alerts.yml   ← hourly cron definition
```

---

## Troubleshooting

**No jobs appearing:**
- Check Actions logs for errors
- Try broadening TARGET_ROLES (e.g. just "Product Manager")
- Increase `JOBS_AGE_DAYS` in config.py

**Telegram not working:**
- Make sure you started a chat with the bot first
- Verify chat ID by hitting the getUpdates URL

**Greenhouse 404:**
- Company may have changed their slug or switched ATS
- Check `https://boards.greenhouse.io/{slug}` in your browser

**GitHub Actions not committing:**
- Check repo Settings → Actions → General → Workflow permissions → Read and write
