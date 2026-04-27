#!/usr/bin/env python3
"""
Job Alert Bot — Multi-Profile Edition (v2)
==========================================
Improvements over v1:
  1. Retry logic       — 3-attempt exponential backoff on all fetchers
  2. Gist storage      — seen_jobs.json persisted to GitHub Gist (survives git resets)
  3. AI scoring        — Gemini free API scores each job 1-10; only 7+ gets notified
  4. LinkedIn source   — 4th job source via LinkedIn RSS
  5. Weekly digest     — Sunday summary; run with: python main.py --weekly-digest

Run locally:  python main.py
Weekly:       python main.py --weekly-digest
GitHub cron:  .github/workflows/job_alerts.yml
"""

import os
import json
import time
import argparse
import smtplib
import logging
import requests
import feedparser
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
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
# 1. RETRY LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_with_retry(fetch_fn, *args, retries: int = 3, backoff: float = 2.0) -> list:
    """
    Calls fetch_fn(*args) up to `retries` times.
    Waits backoff * attempt seconds between retries.
    Returns empty list if all attempts fail.
    """
    for attempt in range(1, retries + 1):
        try:
            return fetch_fn(*args)
        except Exception as e:
            if attempt == retries:
                log.error(f"  All {retries} attempts failed for {fetch_fn.__name__}: {e}")
                return []
            wait = backoff * attempt
            log.warning(f"  Attempt {attempt}/{retries} failed ({e}). Retrying in {wait}s…")
            time.sleep(wait)
    return []


# ═══════════════════════════════════════════════════════════════════════════════
# 2. GIST STORAGE — persists seen_jobs.json outside the repo
# ═══════════════════════════════════════════════════════════════════════════════

def _gist_headers() -> dict:
    return {
        "Authorization": f"token {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }


def load_seen() -> dict:
    """Load seen store: { profile_name: [list of job IDs] }"""
    if config.USE_GIST_STORAGE and config.GIST_ID and config.GITHUB_TOKEN:
        try:
            resp = requests.get(
                f"https://api.github.com/gists/{config.GIST_ID}",
                headers=_gist_headers(),
                timeout=15,
            )
            resp.raise_for_status()
            content = resp.json()["files"].get("seen_jobs.json", {}).get("content", "{}")
            data = json.loads(content)
            log.info("Loaded seen_jobs from GitHub Gist.")
            return data.get("profiles", {})
        except Exception as e:
            log.warning(f"Gist load failed ({e}), falling back to local file.")

    # Fallback: local file
    if not os.path.exists(config.SEEN_JOBS_FILE):
        return {}
    with open(config.SEEN_JOBS_FILE) as f:
        return json.load(f).get("profiles", {})


def save_seen(seen: dict) -> None:
    """Persist seen store, trimming each profile to MAX_SEEN_JOBS."""
    trimmed = {k: v[-config.MAX_SEEN_JOBS:] for k, v in seen.items()}
    payload = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "profiles": trimmed,
    }
    total = sum(len(v) for v in trimmed.values())

    if config.USE_GIST_STORAGE and config.GIST_ID and config.GITHUB_TOKEN:
        try:
            resp = requests.patch(
                f"https://api.github.com/gists/{config.GIST_ID}",
                headers=_gist_headers(),
                json={"files": {"seen_jobs.json": {"content": json.dumps(payload, indent=2)}}},
                timeout=15,
            )
            resp.raise_for_status()
            log.info(f"Saved {total} seen IDs → GitHub Gist.")
            return
        except Exception as e:
            log.warning(f"Gist save failed ({e}), falling back to local file.")

    # Fallback: local file
    with open(config.SEEN_JOBS_FILE, "w") as f:
        json.dump(payload, f, indent=2)
    log.info(f"Saved {total} seen IDs → {config.SEEN_JOBS_FILE}")


# ═══════════════════════════════════════════════════════════════════════════════
# ROLE + LOCATION MATCHING
# ═══════════════════════════════════════════════════════════════════════════════

def matches_role(title: str, profile: dict) -> bool:
    t = title.lower()
    if any(kw.lower() in t for kw in profile["exclude_keywords"]):
        return False
    return any(role.lower() in t for role in profile["target_roles"])


def _loc_ok(location: str) -> bool:
    """All sources — US only, no city restriction."""
    return _loc_us(location)


def _loc_us(location: str) -> bool:
    """Broad filter — any US location passes. Used for Greenhouse and Lever."""
    if not location:
        return True
    loc = location.lower()
    # Explicit non-US countries — reject these
    non_us = [
        "canada", "united kingdom", "uk", "london", "toronto", "vancouver",
        "berlin", "germany", "paris", "france", "amsterdam", "netherlands",
        "dublin", "ireland", "sydney", "australia", "singapore", "india",
        "bangalore", "mumbai", "brazil", "mexico", "japan", "tokyo",
        "china", "beijing", "shanghai", "poland", "romania", "spain",
        "italy", "sweden", "norway", "denmark", "portugal", "israel",
    ]
    if any(country in loc for country in non_us):
        return False
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# 3. AI SCORING — Gemini free API
# ═══════════════════════════════════════════════════════════════════════════════

def score_job(job: dict, profile: dict) -> int:
    """
    Scores a job 1-10 using Gemini 1.5 Flash (free tier).
    Returns 10 (pass-through) if AI scoring is disabled or API key missing.
    Returns 10 on API error so jobs are never silently dropped.
    """
    if not config.AI_SCORING_ENABLED or not config.GEMINI_API_KEY:
        return 10

    prompt = f"""You are a job fit scorer. Score this job 1-10 for this candidate.

Candidate profile:
{profile.get('resume_summary', '')}

Job:
Title: {job['title']}
Company: {job['company']}
Location: {job['location']}

Scoring guide:
9-10 = Perfect match (title + seniority + domain all align, company known to sponsor visas)
7-8  = Strong match (title matches, minor differences)
5-6  = Partial match (related role but not ideal)
1-4  = Poor match (wrong level, domain, role type, or requires US citizenship/clearance)

Important: If the candidate needs visa sponsorship (F1/OPT or H1B transfer) and the job
explicitly requires US citizenship, security clearance, or states no sponsorship,
score it 1-2. Large tech companies (FAANG, Microsoft, Google, etc.) generally sponsor visas.
Defense contractors (Raytheon, Lockheed, Booz Allen) generally do not.

Reply with ONLY a single integer between 1 and 10. No explanation."""

    try:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={config.GEMINI_API_KEY}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=10,
        )
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        score = int("".join(filter(str.isdigit, text[:3])))
        return min(max(score, 1), 10)
    except Exception as e:
        log.warning(f"  Gemini scoring failed for '{job['title']}': {e} — passing through")
        return 10


# ═══════════════════════════════════════════════════════════════════════════════
# FETCHERS
# ═══════════════════════════════════════════════════════════════════════════════

def _salary_too_low(text: str) -> bool:
    """
    Returns True if the text explicitly mentions a salary BELOW the threshold.
    Only drops jobs that clearly state a low salary — never drops ambiguous ones.
    """
    import re
    # Find salary patterns like $80,000 $95k $85K
    matches = re.findall(r'\$(\d+)[,.]?(\d*)[kK]?', text)
    for major, minor in matches:
        try:
            amount = int(major.replace(',', ''))
            if minor:
                amount = int(f"{major}{minor}".replace(',', ''))
            # Normalize: $110 means $110 (already in thousands if < 1000)
            if amount < 1000:
                amount *= 1000
            if amount < config.MIN_SALARY_USD:
                return True
        except ValueError:
            continue
    return False


def fetch_jobicy(role_query: str, profile: dict) -> list[dict]:
    """
    Fetches US remote/hybrid jobs from Jobicy free public API.
    Docs: https://jobicy.com/api/v2/remote-jobs
    """
    url = (
        f"https://jobicy.com/api/v2/remote-jobs"
        f"?count=50"
        f"&geo=usa"
        f"&industry=management"
        f"&tag={role_query}"
    )
    jobs = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        for job in resp.json().get("jobs", []):
            title = job.get("jobTitle", "")
            if not matches_role(title, profile):
                continue
            location = job.get("jobGeo", "USA")
            jobs.append({
                "id": str(job.get("id", "")),
                "title": title,
                "company": job.get("companyName", ""),
                "location": location,
                "url": job.get("url", ""),
                "source": "Jobicy",
                "posted": job.get("pubDate", "")[:10],
                "score": None,
            })
        log.info(f"  Jobicy     | {role_query:<25} | {len(jobs):>3} matched")
    except Exception as e:
        log.warning(f"  Jobicy fetch failed: {e}")
    return jobs


def fetch_indeed(company: str, query: str, profile: dict) -> list[dict]:
    url = (
        f"https://www.indeed.com/rss"
        f"?q={query}"
        f"&l={config.LOCATION_INDEED}"
        f"&sort=date"
        f"&fromage={config.JOBS_AGE_DAYS}"
        f"&salaryType={config.INDEED_MIN_SALARY}"
    )
    jobs = []
    feed = feedparser.parse(url)
    for entry in feed.entries:
        title = entry.get("title", "")
        if not matches_role(title, profile):
            continue
        # Backup salary filter — drop jobs explicitly listing salary below threshold
        summary = entry.get("summary", "") + title
        if _salary_too_low(summary):
            continue
        jobs.append({
            "id": entry.get("id") or entry.get("link"),
            "title": title,
            "company": company,
            "location": entry.get("location", "USA"),
            "url": entry.get("link", ""),
            "source": "Indeed",
            "posted": entry.get("published", ""),
            "score": None,
        })
    log.info(f"  Indeed     | {company:<25} | {len(jobs):>3} matched")
    return jobs


def fetch_greenhouse(company: str, slug: str, profile: dict) -> list[dict]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    jobs = []
    for job in resp.json().get("jobs", []):
        title = job.get("title", "")
        if not matches_role(title, profile):
            continue
        location = job.get("location", {}).get("name", "")
        if not _loc_us(location):
            continue
        jobs.append({
            "id": str(job.get("id")),
            "title": title,
            "company": company,
            "location": location or "USA",
            "url": job.get("absolute_url", ""),
            "source": "Greenhouse",
            "posted": job.get("updated_at", "")[:10],
            "score": None,
        })
    log.info(f"  Greenhouse | {company:<25} | {len(jobs):>3} matched")
    return jobs


def fetch_lever(company: str, slug: str, profile: dict) -> list[dict]:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json&limit=200"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    jobs = []
    for job in resp.json():
        title = job.get("text", "")
        if not matches_role(title, profile):
            continue
        location = job.get("categories", {}).get("location", "")
        if not _loc_us(location):
            continue
        ts = job.get("createdAt", 0)
        posted = (
            datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
            if ts else ""
        )
        jobs.append({
            "id": job.get("id", ""),
            "title": title,
            "company": company,
            "location": location or "USA",
            "url": job.get("hostedUrl", ""),
            "source": "Lever",
            "posted": posted,
            "score": None,
        })
    log.info(f"  Lever      | {company:<25} | {len(jobs):>3} matched")
    return jobs


# ── 4. JobSpy — LinkedIn, Glassdoor, ZipRecruiter, Google Jobs ───────────────

def fetch_jobspy(search_term: str, profile: dict, sites: list = None) -> list[dict]:
    """
    Uses python-jobspy to scrape LinkedIn, Indeed, Glassdoor, ZipRecruiter.
    Free, no API key needed. Used instead of broken LinkedIn RSS.
    """
    if sites is None:
        sites = ["linkedin", "glassdoor", "zip_recruiter"]
    try:
        from jobspy import scrape_jobs
        df = scrape_jobs(
            site_name=sites,
            search_term=search_term,
            location="United States",
            results_wanted=config.JOBSPY_RESULTS_PER_SEARCH,
            hours_old=config.JOBS_AGE_DAYS * 24,
            country_indeed="USA",
            linkedin_fetch_description=False,  # faster without full description
            verbose=0,
        )
        jobs = []
        for _, row in df.iterrows():
            title = str(row.get("title", "") or "")
            if not matches_role(title, profile):
                continue
            location = str(row.get("location", "") or "USA")
            if not _loc_us(location):
                continue
            company  = str(row.get("company", "") or "")
            url      = str(row.get("job_url", "") or "")
            source   = str(row.get("site", "") or "JobSpy").title()
            posted   = str(row.get("date_posted", "") or "")[:10]
            job_id   = str(row.get("id", "") or url)
            jobs.append({
                "id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "url": url,
                "source": source,
                "posted": posted,
                "score": None,
            })
        log.info(f"  JobSpy     | {search_term:<25} | {len(jobs):>3} matched ({', '.join(sites)})")
        return jobs
    except ImportError:
        log.error("  JobSpy not installed — run: pip install python-jobspy")
        return []
    except Exception as e:
        log.warning(f"  JobSpy     | {search_term:<25} | ERROR: {e}")
        return []


# Keep fetch_linkedin as a no-op stub so config entries don't crash
def fetch_linkedin(company: str, query: str, profile: dict) -> list[dict]:
    return []  # Replaced by fetch_jobspy


# ═══════════════════════════════════════════════════════════════════════════════
# EMAIL NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _sanitize(text: str) -> str:
    """Remove non-ASCII characters that break SMTP encoding."""
    return text.encode("ascii", "ignore").decode("ascii").strip() if isinstance(text, str) else text


def _build_html(jobs: list[dict], profile_label: str, subject_prefix: str = "New") -> str:
    rows = ""
    for j in jobs:
        j = {k: _sanitize(v) if isinstance(v, str) else v for k, v in j.items()}
        score_badge = ""
        if j.get("score") is not None:
            color = "#22c55e" if j["score"] >= 8 else "#f59e0b"
            score_badge = f'<span style="background:{color};color:#fff;border-radius:4px;padding:1px 6px;font-size:11px;margin-left:6px;">{j["score"]}/10</span>'
        rows += f"""
        <tr>
          <td style="padding:10px 8px;border-bottom:1px solid #eee;">
            <a href="{j['url']}" style="font-weight:600;color:#0066cc;text-decoration:none;">
              {j['title']}
            </a>{score_badge}<br>
            <span style="color:#555;font-size:13px;">{j['company']} &nbsp;·&nbsp; {j['location']}</span>
          </td>
          <td style="padding:10px 8px;border-bottom:1px solid #eee;font-size:12px;color:#888;white-space:nowrap;">
            {j['source']}
          </td>
          <td style="padding:10px 8px;border-bottom:1px solid #eee;font-size:12px;color:#888;white-space:nowrap;">
            {str(j.get('posted',''))[:10]}
          </td>
        </tr>"""

    run_time = datetime.now(timezone.utc).strftime("%b %d, %Y %H:%M UTC")
    return f"""
<html><body style="font-family:Arial,sans-serif;color:#222;margin:0;padding:20px;">
  <h2 style="color:#1a1a2e;margin-bottom:4px;">
    🚀 {len(jobs)} {subject_prefix} <span style="color:#0066cc;">{profile_label}</span>
    job{'s' if len(jobs) != 1 else ''}
  </h2>
  <p style="color:#888;font-size:13px;margin-top:0;">
    {run_time} &nbsp;·&nbsp; {config.LOCATION}
    {"&nbsp;·&nbsp; AI scored ≥ " + str(config.AI_SCORE_THRESHOLD) + "/10" if config.AI_SCORING_ENABLED else ""}
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
  <p style="color:#aaa;font-size:11px;margin-top:20px;">Job Alert Bot v2 · Automated</p>
</body></html>"""


def send_email(jobs: list[dict], to_addr: str, profile_label: str, subject_prefix: str = "New") -> None:
    user     = os.environ.get("GMAIL_USER")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not password:
        log.warning("Gmail: GMAIL_USER or GMAIL_APP_PASSWORD not set — skipping.")
        return

    location = _sanitize(config.LOCATION)
    label    = _sanitize(profile_label)
    prefix   = _sanitize(subject_prefix)

    subject = (
        f"[Job Alert | {label}] "
        f"{len(jobs)} {prefix.lower()} role{'s' if len(jobs) != 1 else ''} in {location}"
    )
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = user
    msg["To"]      = to_addr
    plain = "\n".join(
        f"- {_sanitize(j['title'])} @ {_sanitize(j['company'])} -- {j['url']}"
        for j in jobs
    )
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(_build_html(jobs, profile_label, subject_prefix), "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
            srv.login(user, password)
            srv.send_message(msg)
        log.info(f"  Email sent → {to_addr}")
    except Exception as e:
        import traceback
        log.error(f"  Gmail failed → {to_addr}: {e}")
        log.error(f"  Traceback:\n{traceback.format_exc()}")


def send_telegram(jobs: list[dict], profile_label: str) -> None:
    token   = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        log.warning("Telegram: secrets not set — skipping.")
        return

    base_url = f"https://api.telegram.org/bot{token}/sendMessage"
    score_note = " _(AI scored ≥ 7/10)_" if config.AI_SCORING_ENABLED else ""
    header = f"🚀 *{len(jobs)} new {profile_label} job{'s' if len(jobs) != 1 else ''}*{score_note} in {config.LOCATION}\n\n"
    chunks = [jobs[i:i+10] for i in range(0, len(jobs), 10)]

    for idx, chunk in enumerate(chunks):
        lines = []
        for j in chunk:
            score_str = f" · Score: {j['score']}/10" if j.get("score") else ""
            lines.append(
                f"*{j['title']}*{score_str}\n"
                f"🏢 {j['company']} 📍 {j['location']}\n"
                f"🔗 [Apply →]({j['url']})"
            )
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
# 5. WEEKLY DIGEST
# ═══════════════════════════════════════════════════════════════════════════════

def send_weekly_digest(profile_name: str, profile: dict, seen_store: dict) -> None:
    """
    Sends a Sunday summary of all jobs seen in the past 7 days.
    seen_store entries need a 'seen_date' field (added in v2).
    """
    log.info(f"  Generating weekly digest for {profile['label']}…")
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    profile_seen = seen_store.get(profile_name, {})

    # Support both old format (list of IDs) and new format (list of dicts)
    if isinstance(profile_seen, list):
        log.info("  No enriched job data available yet — run hourly bot first.")
        return

    recent_jobs = [
        j for j in profile_seen.values()
        if isinstance(j, dict) and
        datetime.fromisoformat(j.get("seen_date", "2000-01-01")).replace(tzinfo=timezone.utc) >= cutoff
    ]

    if not recent_jobs:
        log.info(f"  No jobs in past 7 days for {profile['label']}.")
        return

    if config.NOTIFY_GMAIL:
        send_email(recent_jobs, profile["notify_email"], profile["label"], subject_prefix="Weekly digest —")
    log.info(f"  Weekly digest sent: {len(recent_jobs)} jobs.")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PROFILE RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

def run_profile(profile_name: str, profile: dict, seen_for_profile: set) -> set:
    label     = profile["label"]
    companies = profile["companies"]
    log.info(f"  Fetching {len(companies)} companies…")

    all_jobs: list[dict] = []
    for company, cfg in companies.items():
        try:
            if cfg["type"] == "indeed":
                jobs = fetch_with_retry(fetch_indeed, company, cfg["query"], profile)
            elif cfg["type"] == "greenhouse":
                jobs = fetch_with_retry(fetch_greenhouse, company, cfg["slug"], profile)
            elif cfg["type"] == "lever":
                jobs = fetch_with_retry(fetch_lever, company, cfg["slug"], profile)
            elif cfg["type"] == "linkedin":
                jobs = fetch_with_retry(fetch_linkedin, company, cfg["query"], profile)
            else:
                log.warning(f"  Unknown type '{cfg['type']}' for {company}")
                jobs = []
            all_jobs.extend(jobs)
        except Exception as e:
            log.error(f"  Unhandled error [{company}]: {e}")
        time.sleep(0.3)

    # Fetch from Jobicy — rate limited to first query only (429 protection)
    jobicy_queries = profile.get("jobicy_queries", [])
    if jobicy_queries:
        try:
            jobicy_jobs = fetch_with_retry(fetch_jobicy, jobicy_queries[0], profile)
            all_jobs.extend(jobicy_jobs)
        except Exception as e:
            log.error(f"  Jobicy error: {e}")
        time.sleep(3.0)  # respect rate limit

    # Fetch from JobSpy — LinkedIn, Glassdoor, ZipRecruiter (free, no API key)
    for query in profile.get("jobspy_queries", []):
        try:
            spy_jobs = fetch_jobspy(query, profile)
            all_jobs.extend(spy_jobs)
        except Exception as e:
            log.error(f"  JobSpy error: {e}")
        time.sleep(5.0)  # be polite between searches

    log.info(f"  Total fetched: {len(all_jobs)}")

    # Dedup
    seen_this_run: set[str] = set()
    new_jobs: list[dict] = []
    for j in all_jobs:
        if j["id"] not in seen_for_profile and j["id"] not in seen_this_run:
            new_jobs.append(j)
            seen_this_run.add(j["id"])

    log.info(f"  New (not seen before): {len(new_jobs)}")

    # AI scoring
    if config.AI_SCORING_ENABLED and config.GEMINI_API_KEY and new_jobs:
        log.info(f"  Scoring {len(new_jobs)} jobs with Gemini…")
        scored = []
        for j in new_jobs:
            j["score"] = score_job(j, profile)
            log.info(f"    {j['score']}/10 — {j['title']} @ {j['company']}")
            time.sleep(0.2)   # gentle rate limiting
        new_jobs = [j for j in new_jobs if j["score"] >= config.AI_SCORE_THRESHOLD]
        log.info(f"  After AI filter (≥{config.AI_SCORE_THRESHOLD}): {len(new_jobs)} jobs")

    # Cap
    if len(new_jobs) > config.MAX_JOBS_PER_RUN:
        log.info(f"  Capping to {config.MAX_JOBS_PER_RUN}")
        new_jobs = new_jobs[:config.MAX_JOBS_PER_RUN]

    # Notify
    if new_jobs:
        if config.NOTIFY_GMAIL:
            send_email(new_jobs, profile["notify_email"], label)
        if config.NOTIFY_TELEGRAM:
            send_telegram(new_jobs, label)
    elif config.SEND_EMPTY_DIGEST and config.NOTIFY_GMAIL:
        send_email([], profile["notify_email"], label)

    # Update seen
    for j in all_jobs:
        seen_for_profile.add(j["id"])

    return seen_for_profile


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--weekly-digest", action="store_true",
                        help="Send weekly summary instead of hourly alerts")
    args = parser.parse_args()

    log.info("=" * 62)
    log.info(f"Job Alert Bot v2 — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    log.info(f"Location: {config.LOCATION} | Remote OK: {config.REMOTE_OK}")
    log.info(f"AI Scoring: {'ON (threshold=' + str(config.AI_SCORE_THRESHOLD) + '/10)' if config.AI_SCORING_ENABLED else 'OFF'}")
    log.info(f"Storage: {'GitHub Gist' if config.USE_GIST_STORAGE and config.GIST_ID else 'Local file'}")
    log.info(f"Active profiles: {[k for k, v in config.PROFILES.items() if v.get('active')]}")
    log.info("=" * 62)

    seen_store = load_seen()

    if args.weekly_digest:
        for profile_name, profile in config.PROFILES.items():
            if not profile.get("active", True):
                continue
            log.info(f"\n{'─'*50}")
            log.info(f"WEEKLY DIGEST: {profile['label']}")
            log.info(f"{'─'*50}")
            send_weekly_digest(profile_name, profile, seen_store)
        return

    for profile_name, profile in config.PROFILES.items():
        if not profile.get("active", True):
            log.info(f"\n[{profile['label']}] — SKIPPED (inactive)")
            continue

        log.info(f"\n{'─'*50}")
        log.info(f"PROFILE: {profile['label']} → {profile['notify_email']}")
        log.info(f"{'─'*50}")

        seen_ids = set(seen_store.get(profile_name, []))
        log.info(f"  Previously seen: {len(seen_ids)} job IDs")

        updated_seen = run_profile(profile_name, profile, seen_ids)
        seen_store[profile_name] = list(updated_seen)

    save_seen(seen_store)
    log.info("\nAll profiles done.")


if __name__ == "__main__":
    main()