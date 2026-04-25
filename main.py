#!/usr/bin/env python3
"""
Job Alert Bot  —  Multi-Profile Edition
========================================
Runs each PROFILE independently:
  • product_manager  →  pmhritvik@gmail.com
  • sde2             →  navadityagaur@gmail.com

Each profile has its own roles, companies, and email destination.
Deduplication is per-profile so a job won't be re-sent even if it
shows up in multiple fetch cycles.

Run locally:   python main.py
GitHub Actions cron: .github/workflows/job_alerts.yml
"""

import os
import json
import time
import smtplib
import logging
import requests
import feedparser
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


# ═══════════════════════════════════════════════════════════════════════════════
#  ROLE MATCHING  (per-profile)
# ═══════════════════════════════════════════════════════════════════════════════

def matches_role(title: str, profile: dict) -> bool:
    """Return True if title matches a target role and none of the exclude keywords."""
    t = title.lower()
    if any(kw.lower() in t for kw in profile["exclude_keywords"]):
        return False
    return any(role.lower() in t for role in profile["target_roles"])


# ═══════════════════════════════════════════════════════════════════════════════
#  FETCHERS
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_indeed(company: str, query: str, profile: dict) -> list[dict]:
    url = (
        f"https://www.indeed.com/rss"
        f"?q={query}"
        f"&l={config.LOCATION_INDEED}"
        f"&sort=date"
        f"&fromage={config.JOBS_AGE_DAYS}"
    )
    jobs = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.get("title", "")
            if not matches_role(title, profile):
                continue
            jobs.append({
                "id":       entry.get("id") or entry.get("link"),
                "title":    title,
                "company":  company,
                "location": entry.get("location", config.LOCATION),
                "url":      entry.get("link", ""),
                "source":   "Indeed",
                "posted":   entry.get("published", ""),
            })
        log.info(f"  Indeed     | {company:<22} | {len(jobs):>3} matched")
    except Exception as e:
        log.warning(f"  Indeed     | {company:<22} | ERROR: {e}")
    return jobs


def fetch_greenhouse(company: str, slug: str, profile: dict) -> list[dict]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    jobs = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        for job in resp.json().get("jobs", []):
            title = job.get("title", "")
            if not matches_role(title, profile):
                continue
            location = job.get("location", {}).get("name", "")
            if not _loc_ok(location):
                continue
            jobs.append({
                "id":       str(job.get("id")),
                "title":    title,
                "company":  company,
                "location": location or config.LOCATION,
                "url":      job.get("absolute_url", ""),
                "source":   "Greenhouse",
                "posted":   job.get("updated_at", "")[:10],
            })
        log.info(f"  Greenhouse | {company:<22} | {len(jobs):>3} matched")
    except Exception as e:
        log.warning(f"  Greenhouse | {company:<22} | ERROR: {e}")
    return jobs


def fetch_lever(company: str, slug: str, profile: dict) -> list[dict]:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json&limit=200"
    jobs = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        for job in resp.json():
            title = job.get("text", "")
            if not matches_role(title, profile):
                continue
            location = job.get("categories", {}).get("location", "")
            if not _loc_ok(location):
                continue
            ts = job.get("createdAt", 0)
            posted = (
                datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
                if ts else ""
            )
            jobs.append({
                "id":       job.get("id", ""),
                "title":    title,
                "company":  company,
                "location": location or config.LOCATION,
                "url":      job.get("hostedUrl", ""),
                "source":   "Lever",
                "posted":   posted,
            })
        log.info(f"  Lever      | {company:<22} | {len(jobs):>3} matched")
    except Exception as e:
        log.warning(f"  Lever      | {company:<22} | ERROR: {e}")
    return jobs


def _loc_ok(location: str) -> bool:
    """Accept if location is blank, matches config.LOCATION, or is Remote."""
    if not location:
        return True
    loc = location.lower()
    if config.LOCATION.lower() in loc:
        return True
    if config.REMOTE_OK and "remote" in loc:
        return True
    return False


# ═══════════════════════════════════════════════════════════════════════════════
#  DEDUP STORE  —  keyed by profile name so profiles don't share state
# ═══════════════════════════════════════════════════════════════════════════════

def load_seen() -> dict:
    """Load full seen store: { profile_name: [list of job IDs] }"""
    path = config.SEEN_JOBS_FILE
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f).get("profiles", {})


def save_seen(seen: dict) -> None:
    """Persist seen store, trimming each profile to MAX_SEEN_JOBS."""
    trimmed = {
        k: v[-config.MAX_SEEN_JOBS:] for k, v in seen.items()
    }
    with open(config.SEEN_JOBS_FILE, "w") as f:
        json.dump(
            {
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "profiles": trimmed,
            },
            f,
            indent=2,
        )
    total = sum(len(v) for v in trimmed.values())
    log.info(f"Saved {total} total seen job IDs → {config.SEEN_JOBS_FILE}")


# ═══════════════════════════════════════════════════════════════════════════════
#  EMAIL NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _build_html(jobs: list[dict], profile_label: str) -> str:
    rows = ""
    for j in jobs:
        rows += f"""
        <tr>
          <td style="padding:10px 8px;border-bottom:1px solid #eee;">
            <a href="{j['url']}" style="font-weight:600;color:#0066cc;text-decoration:none;">
              {j['title']}
            </a><br>
            <span style="color:#555;font-size:13px;">{j['company']} &nbsp;·&nbsp; {j['location']}</span>
          </td>
          <td style="padding:10px 8px;border-bottom:1px solid #eee;font-size:12px;color:#888;white-space:nowrap;">
            {j['source']}
          </td>
          <td style="padding:10px 8px;border-bottom:1px solid #eee;font-size:12px;color:#888;white-space:nowrap;">
            {j.get('posted','')[:10]}
          </td>
        </tr>"""

    run_time = datetime.now(timezone.utc).strftime("%b %d, %Y  %H:%M UTC")
    return f"""
    <html><body style="font-family:Arial,sans-serif;color:#222;margin:0;padding:20px;">
      <h2 style="color:#1a1a2e;margin-bottom:4px;">
        🚀 {len(jobs)} new <span style="color:#0066cc;">{profile_label}</span>
        job{'s' if len(jobs)!=1 else ''}
      </h2>
      <p style="color:#888;font-size:13px;margin-top:0;">
        Fetched: {run_time} &nbsp;·&nbsp; Location: {config.LOCATION}
      </p>
      <table style="width:100%;border-collapse:collapse;margin-top:16px;">
        <thead>
          <tr style="background:#f5f5f5;">
            <th style="padding:10px 8px;text-align:left;font-size:13px;color:#555;">Role &amp; Company</th>
            <th style="padding:10px 8px;text-align:left;font-size:13px;color:#555;">Source</th>
            <th style="padding:10px 8px;text-align:left;font-size:13px;color:#555;">Posted</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
      <p style="color:#aaa;font-size:11px;margin-top:20px;">Job Alert Bot · Automated</p>
    </body></html>
    """


def send_email(jobs: list[dict], to_addr: str, profile_label: str) -> None:
    """Send a styled HTML digest to the profile's destination email."""
    user     = os.environ.get("GMAIL_USER")
    password = os.environ.get("GMAIL_APP_PASSWORD")

    if not user or not password:
        log.warning("Gmail: GMAIL_USER or GMAIL_APP_PASSWORD not set — skipping.")
        return

    subject = (
        f"[Job Alert | {profile_label}] "
        f"{len(jobs)} new role{'s' if len(jobs)!=1 else ''} in {config.LOCATION}"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = user
    msg["To"]      = to_addr

    plain = "\n".join(f"• {j['title']} @ {j['company']} — {j['url']}" for j in jobs)
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(_build_html(jobs, profile_label), "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
            srv.login(user, password)
            srv.sendmail(user, to_addr, msg.as_string())
        log.info(f"  Email sent → {to_addr}")
    except Exception as e:
        log.error(f"  Gmail failed → {to_addr} : {e}")


def send_telegram(jobs: list[dict], profile_label: str) -> None:
    """Send Telegram message for a profile's new jobs."""
    token   = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        log.warning("Telegram: secrets not set — skipping.")
        return

    base_url = f"https://api.telegram.org/bot{token}/sendMessage"
    header   = f"🚀 *{len(jobs)} new {profile_label} job{'s' if len(jobs)!=1 else ''}* in {config.LOCATION}\n\n"
    chunks   = [jobs[i:i+10] for i in range(0, len(jobs), 10)]

    for idx, chunk in enumerate(chunks):
        lines = [
            f"*{j['title']}*\n🏢 {j['company']}  📍 {j['location']}\n🔗 [Apply →]({j['url']})"
            for j in chunk
        ]
        body = (header if idx == 0 else f"_(part {idx+1}/{len(chunks)})_\n\n") + "\n\n".join(lines)
        try:
            resp = requests.post(
                base_url,
                json={"chat_id": chat_id, "text": body, "parse_mode": "Markdown",
                      "disable_web_page_preview": True},
                timeout=10,
            )
            resp.raise_for_status()
            log.info(f"  Telegram chunk {idx+1}/{len(chunks)} sent")
        except Exception as e:
            log.error(f"  Telegram chunk {idx+1} failed: {e}")
        time.sleep(0.5)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN — runs every profile in sequence
# ═══════════════════════════════════════════════════════════════════════════════

def run_profile(profile_name: str, profile: dict, seen_for_profile: set) -> set:
    """Fetch, filter, notify and return updated seen set for one profile."""
    label     = profile["label"]
    companies = profile["companies"]

    log.info(f"  Fetching {len(companies)} companies…")

    all_jobs: list[dict] = []
    for company, cfg in companies.items():
        try:
            if cfg["type"] == "indeed":
                all_jobs.extend(fetch_indeed(company, cfg["query"], profile))
            elif cfg["type"] == "greenhouse":
                all_jobs.extend(fetch_greenhouse(company, cfg["slug"], profile))
            elif cfg["type"] == "lever":
                all_jobs.extend(fetch_lever(company, cfg["slug"], profile))
        except Exception as e:
            log.error(f"  Unhandled error [{company}]: {e}")
        time.sleep(0.3)

    log.info(f"  Total fetched: {len(all_jobs)}")

    # Filter new and deduplicate within this run
    seen_this_run: set[str] = set()
    new_jobs: list[dict] = []
    for j in all_jobs:
        if j["id"] not in seen_for_profile and j["id"] not in seen_this_run:
            new_jobs.append(j)
            seen_this_run.add(j["id"])

    log.info(f"  New (not seen before): {len(new_jobs)}")

    if len(new_jobs) > config.MAX_JOBS_PER_RUN:
        log.info(f"  Capping to {config.MAX_JOBS_PER_RUN}")
        new_jobs = new_jobs[: config.MAX_JOBS_PER_RUN]

    # Notify
    if new_jobs:
        if config.NOTIFY_GMAIL:
            send_email(new_jobs, profile["notify_email"], label)
        if config.NOTIFY_TELEGRAM:
            send_telegram(new_jobs, label)
    elif config.SEND_EMPTY_DIGEST and config.NOTIFY_GMAIL:
        send_email([], profile["notify_email"], label)

    # Update seen set with ALL jobs fetched this run (not just new ones)
    for j in all_jobs:
        seen_for_profile.add(j["id"])

    return seen_for_profile


def main() -> None:
    log.info("=" * 62)
    log.info(f"Job Alert Bot  —  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    log.info(f"Location: {config.LOCATION}  |  Remote OK: {config.REMOTE_OK}")
    log.info(f"Active profiles: {[k for k,v in config.PROFILES.items() if v.get('active')]}")
    log.info("=" * 62)

    # Load seen store (dict keyed by profile name)
    seen_store = load_seen()

    for profile_name, profile in config.PROFILES.items():
        if not profile.get("active", True):
            log.info(f"\n[{profile['label']}] — SKIPPED (inactive)")
            continue

        log.info(f"\n{'─'*50}")
        log.info(f"PROFILE: {profile['label']}  →  {profile['notify_email']}")
        log.info(f"{'─'*50}")

        seen_ids = set(seen_store.get(profile_name, []))
        log.info(f"  Previously seen: {len(seen_ids)} job IDs")

        updated_seen = run_profile(profile_name, profile, seen_ids)
        seen_store[profile_name] = list(updated_seen)

    # Persist updated seen store
    save_seen(seen_store)
    log.info("\nAll profiles done.")


if __name__ == "__main__":
    main()
