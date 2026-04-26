"""
config.py — All customization lives here.
==========================================
Profiles, companies, roles, notification settings.
"""

import os

# ── Location ──────────────────────────────────────────────────────────────────
LOCATION        = "Seattle, WA"
LOCATION_INDEED = "Seattle%2C+WA"
REMOTE_OK       = True
JOBS_AGE_DAYS   = 3

# ── Dedup / Storage ───────────────────────────────────────────────────────────
SEEN_JOBS_FILE  = "seen_jobs.json"
MAX_SEEN_JOBS   = 5000      # per profile, older IDs are trimmed
MAX_JOBS_PER_RUN = 50       # cap alerts per run to avoid spam

# Use GitHub Gist for persistent dedup storage (survives git resets)
USE_GIST_STORAGE = True
GIST_ID          = os.environ.get("GIST_ID", "")          # GitHub Secret
GITHUB_TOKEN     = os.environ.get("GITHUB_TOKEN", "")     # GitHub Secret

# ── Notifications ─────────────────────────────────────────────────────────────
NOTIFY_GMAIL     = True
NOTIFY_TELEGRAM  = True
SEND_EMPTY_DIGEST = False   # set True to get "no new jobs" emails

# ── AI Scoring (Gemini free tier) ─────────────────────────────────────────────
AI_SCORING_ENABLED  = True
AI_SCORE_THRESHOLD  = 7     # only notify jobs scoring >= this (out of 10)
GEMINI_API_KEY      = os.environ.get("GEMINI_API_KEY", "")  # GitHub Secret

# ── Profiles ──────────────────────────────────────────────────────────────────
PROFILES = {

    "product_manager": {
        "active": True,
        "label": "Senior PM",
        "notify_email": "pmhritvik@gmail.com",
        "resume_summary": (
            "7+ years founder experience across EdTech, PropTech, Biotech. "
            "MS Information Management (AI & PM) University of Washington 2026. "
            "Shipped 20+ features, led teams of 12-20, drove 19% conversion lifts. "
            "Targeting Senior PM / Group PM roles at FAANG in Seattle."
        ),
        "target_roles": [
            "Senior Product Manager",
            "Senior PM",
            "Group Product Manager",
            "Group PM",
            "Principal Product Manager",
            "Principal PM",
            "Product Lead",
            "Director of Product",
        ],
        "exclude_keywords": [
            "intern", "internship", "junior", "associate pm",
            "marketing", "growth hacker", "sales",
        ],
        "companies": {
            # ── Greenhouse ───────────────────────────────────────────────────
            "Airbnb":       {"type": "greenhouse", "slug": "airbnb"},
            "Figma":        {"type": "greenhouse", "slug": "figma"},
            "Coinbase":     {"type": "greenhouse", "slug": "coinbase"},
            "Robinhood":    {"type": "greenhouse", "slug": "robinhood"},
            "Stripe":       {"type": "greenhouse", "slug": "stripe"},
            "DoorDash":     {"type": "greenhouse", "slug": "doordash"},
            "Notion":       {"type": "greenhouse", "slug": "notion"},
            "Dropbox":      {"type": "greenhouse", "slug": "dropbox"},
            "Pinterest":    {"type": "greenhouse", "slug": "pinterest"},
            "Lyft":         {"type": "greenhouse", "slug": "lyft"},
            "Twilio":       {"type": "greenhouse", "slug": "twilio"},
            "Cloudflare":   {"type": "greenhouse", "slug": "cloudflare"},
            "Datadog":      {"type": "greenhouse", "slug": "datadog"},
            "HashiCorp":    {"type": "greenhouse", "slug": "hashicorp"},
            # ── Lever ────────────────────────────────────────────────────────
            "Waymo":        {"type": "lever", "slug": "waymo"},
            "Rippling":     {"type": "lever", "slug": "rippling"},
            "Scale AI":     {"type": "lever", "slug": "scaleai"},
            "Anduril":      {"type": "lever", "slug": "anduril"},
            # ── Indeed fallback ──────────────────────────────────────────────
            "Amazon":       {"type": "indeed", "query": "amazon+senior+product+manager"},
            "Microsoft":    {"type": "indeed", "query": "microsoft+senior+product+manager"},
            "Google":       {"type": "indeed", "query": "google+senior+product+manager"},
            "Meta":         {"type": "indeed", "query": "meta+senior+product+manager"},
            "Apple":        {"type": "indeed", "query": "apple+senior+product+manager"},
            "Netflix":      {"type": "indeed", "query": "netflix+senior+product+manager"},
            "Uber":         {"type": "indeed", "query": "uber+senior+product+manager"},
            "Zillow":       {"type": "indeed", "query": "zillow+product+manager"},
            "Twitch":       {"type": "indeed", "query": "twitch+amazon+product+manager"},
            # ── LinkedIn ─────────────────────────────────────────────────────
            "Amazon (LinkedIn)":   {"type": "linkedin", "query": "Amazon+Senior+Product+Manager"},
            "Microsoft (LinkedIn)":{"type": "linkedin", "query": "Microsoft+Senior+Product+Manager"},
            "Apple (LinkedIn)":    {"type": "linkedin", "query": "Apple+Senior+Product+Manager"},
        },
    },

    "sde2": {
        "active": True,
        "label": "SDE-2",
        "notify_email": "navadityagaur@gmail.com",
        "resume_summary": (
            "Software engineer with full-stack and backend experience. "
            "Python, TypeScript, Firebase, React Native. "
            "Targeting SDE-2 / Software Engineer II roles at FAANG in Seattle."
        ),
        "target_roles": [
            "Software Engineer II",
            "SDE-2", "SDE 2",
            "Senior Software Engineer",
            "Software Developer II",
            "Backend Engineer",
            "Full Stack Engineer",
        ],
        "exclude_keywords": [
            "intern", "internship", "junior", "staff", "principal",
            "director", "manager", "lead",
        ],
        "companies": {
            # ── Greenhouse ───────────────────────────────────────────────────
            "Stripe":       {"type": "greenhouse", "slug": "stripe"},
            "Airbnb":       {"type": "greenhouse", "slug": "airbnb"},
            "DoorDash":     {"type": "greenhouse", "slug": "doordash"},
            "Lyft":         {"type": "greenhouse", "slug": "lyft"},
            "Coinbase":     {"type": "greenhouse", "slug": "coinbase"},
            "Cloudflare":   {"type": "greenhouse", "slug": "cloudflare"},
            "Datadog":      {"type": "greenhouse", "slug": "datadog"},
            # ── Lever ────────────────────────────────────────────────────────
            "Scale AI":     {"type": "lever", "slug": "scaleai"},
            "Rippling":     {"type": "lever", "slug": "rippling"},
            # ── Indeed fallback ──────────────────────────────────────────────
            "Amazon":       {"type": "indeed", "query": "amazon+software+engineer+II"},
            "Microsoft":    {"type": "indeed", "query": "microsoft+software+engineer+2"},
            "Google":       {"type": "indeed", "query": "google+software+engineer+II"},
            "Meta":         {"type": "indeed", "query": "meta+software+engineer+E4"},
            "Apple":        {"type": "indeed", "query": "apple+software+engineer+ICT3"},
            "Uber":         {"type": "indeed", "query": "uber+software+engineer+II"},
            # ── LinkedIn ─────────────────────────────────────────────────────
            "Amazon (LinkedIn)":   {"type": "linkedin", "query": "Amazon+Software+Engineer+II"},
            "Microsoft (LinkedIn)":{"type": "linkedin", "query": "Microsoft+Software+Engineer+2"},
        },
    },
}
