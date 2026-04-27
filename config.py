"""
config.py — All customization lives here.
==========================================
Profiles, companies, roles, notification settings.
"""

import os

# ── Location ──────────────────────────────────────────────────────────────────
LOCATION        = "United States"        # display label
LOCATION_INDEED = "United+States"        # Indeed RSS location param — covers all US
REMOTE_OK       = True                   # include US-remote jobs
JOBS_AGE_DAYS      = 3
INDEED_MIN_SALARY  = "%24110%2C000%2B"   # $110,000+ salary filter for Indeed URL
MIN_SALARY_USD     = 110_000              # backup salary filter (drops jobs explicitly < this)

# Top 50 US tech hub cities — jobs matching any of these will be included
TARGET_CITIES = [
    # Pacific Northwest
    "Seattle", "Bellevue", "Redmond", "Kirkland", "Bothell", "Tacoma",
    # Bay Area
    "San Francisco", "San Jose", "Sunnyvale", "Mountain View", "Palo Alto",
    "Menlo Park", "Redwood City", "Santa Clara", "Cupertino", "Foster City",
    "Fremont", "Oakland", "Berkeley",
    # Southern California
    "Los Angeles", "Santa Monica", "Culver City", "Irvine", "San Diego",
    # Pacific
    "Portland", "Honolulu",
    # Mountain West
    "Denver", "Boulder", "Salt Lake City", "Phoenix", "Scottsdale",
    # Texas
    "Austin", "Dallas", "Houston", "San Antonio",
    # Midwest
    "Chicago", "Detroit", "Minneapolis", "Columbus", "Indianapolis",
    # Northeast
    "New York", "Boston", "Cambridge", "Washington DC", "Washington, D.C",
    "Bethesda", "Arlington", "Philadelphia", "Pittsburgh",
    # Southeast
    "Atlanta", "Miami", "Raleigh", "Charlotte", "Nashville",
    # Remote US
    "Remote",
]

# ── Dedup / Storage ───────────────────────────────────────────────────────────
SEEN_JOBS_FILE  = "seen_jobs.json"
MAX_SEEN_JOBS   = 5000      # per profile, older IDs are trimmed
MAX_JOBS_PER_RUN = 50       # cap alerts per run to avoid spam
JOBSPY_RESULTS_PER_SEARCH = 30  # results per JobSpy query (LinkedIn/Glassdoor/ZipRecruiter)

# Use GitHub Gist for persistent dedup storage (survives git resets)
USE_GIST_STORAGE = True
GIST_ID          = os.environ.get("GIST_ID", "")          # GitHub Secret
GITHUB_TOKEN     = os.environ.get("GH_TOKEN", "")     # GitHub Secret

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
            "International F1 student on OPT. MS Information Management (AI & PM) "
            "University of Washington, graduating August 2026. "
            "7+ years founder experience across EdTech, PropTech, Biotech. "
            "Shipped 20+ features, led teams of 12-20, drove 19% conversion lifts. "
            "Requires OPT work authorization and employer willing to sponsor H1B. "
            "Targeting Senior PM / Group PM roles at FAANG in USA."
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
            "us citizen", "u.s. citizen", "clearance required",
            "secret clearance", "top secret", "ts/sci",
            "green card only", "no sponsorship",
        ],
        "jobicy_queries": [
            "product+manager",
            "senior+product+manager",
        ],
        "jobspy_queries": [
            "Senior Product Manager",
            "Group Product Manager",
        ],
        "companies": {
            # ── Greenhouse ───────────────────────────────────────────────────
            "Airbnb":       {"type": "greenhouse", "slug": "airbnb"},
            "Figma":        {"type": "greenhouse", "slug": "figma"},
            "Coinbase":     {"type": "greenhouse", "slug": "coinbase"},
            "Robinhood":    {"type": "greenhouse", "slug": "robinhood"},
            "Stripe":       {"type": "greenhouse", "slug": "stripe"},
            "DoorDash":     {"type": "greenhouse", "slug": "doordashusa"},
            "Notion":       {"type": "indeed", "query": "notion+product+manager"},
            "Dropbox":      {"type": "greenhouse", "slug": "dropbox"},
            "Pinterest":    {"type": "greenhouse", "slug": "pinterest"},
            "Lyft":         {"type": "greenhouse", "slug": "lyft"},
            "Twilio":       {"type": "greenhouse", "slug": "twilio"},
            "Cloudflare":   {"type": "greenhouse", "slug": "cloudflare"},
            "Datadog":      {"type": "greenhouse", "slug": "datadog"},
            "HashiCorp":    {"type": "indeed", "query": "hashicorp+product+manager"},
            # ── Lever ────────────────────────────────────────────────────────
            "Waymo":        {"type": "indeed", "query": "waymo+product+manager"},
            "Rippling":     {"type": "indeed", "query": "rippling+product+manager"},
            "Scale AI":     {"type": "greenhouse", "slug": "scaleai"},
            "Anduril":      {"type": "indeed", "query": "anduril+product+manager"},
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

            # ── AI Labs (Greenhouse) ──────────────────────────────────────────
            "Anthropic":    {"type": "greenhouse", "slug": "anthropic"},
            "Databricks":   {"type": "greenhouse", "slug": "databricks"},
            "Snowflake":    {"type": "indeed", "query": "snowflake+product+manager"},
            "HubSpot":      {"type": "greenhouse", "slug": "hubspot"},
            "Duolingo":     {"type": "greenhouse", "slug": "duolingo"},
            "MongoDB":      {"type": "greenhouse", "slug": "mongodb"},
            "CrowdStrike":  {"type": "indeed", "query": "crowdstrike+product+manager"},
            "Confluent":    {"type": "indeed", "query": "confluent+product+manager"},
            "Palo Alto":    {"type": "indeed", "query": "paloalto+product+manager"},
            "ServiceNow":   {"type": "indeed", "query": "servicenow+product+manager"},
            "Workday":      {"type": "indeed", "query": "workday+product+manager"},

            # ── AI Labs (Lever) ───────────────────────────────────────────────
            "Palantir":     {"type": "lever", "slug": "palantir"},
            "SpaceX":       {"type": "lever", "slug": "spacex-2"},

            # ── Big Tech / Enterprise (Indeed fallback) ───────────────────────
            "OpenAI":       {"type": "indeed", "query": "openai+product+manager"},
            "IBM":          {"type": "indeed", "query": "ibm+product+manager"},
            "Cisco":        {"type": "indeed", "query": "cisco+product+manager"},
            "Oracle":       {"type": "indeed", "query": "oracle+product+manager"},
            "Adobe":        {"type": "indeed", "query": "adobe+product+manager"},
            "Salesforce":   {"type": "indeed", "query": "salesforce+product+manager"},
            "Nvidia":       {"type": "indeed", "query": "nvidia+product+manager"},
            "Intel":        {"type": "indeed", "query": "intel+product+manager"},
            "Tesla":        {"type": "indeed", "query": "tesla+product+manager"},
            "xAI":          {"type": "indeed", "query": "xai+elon+product+manager"},
            "Qualcomm":     {"type": "indeed", "query": "qualcomm+product+manager"},
            "AMD":          {"type": "indeed", "query": "amd+product+manager"},
            "SAP":          {"type": "indeed", "query": "sap+product+manager"},
        },
    },

    "sde2": {
        "active": True,
        "label": "SDE-2",
        "notify_email": "navadityagaur@gmail.com",
        "resume_summary": (
            "Software engineer with H1B work authorization — no sponsorship needed. "
            "Full-stack and backend experience: Python, TypeScript, Firebase, React Native. "
            "H1B transfer welcome. Targeting SDE-2 / Software Engineer II roles at FAANG in USA."
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
            "us citizen", "u.s. citizen", "clearance required",
            "secret clearance", "top secret", "ts/sci",
        ],
        "jobicy_queries": [
            "software+engineer",
            "backend+engineer",
        ],
        "jobspy_queries": [
            "Software Engineer II",
            "Senior Software Engineer",
        ],
        "companies": {
            # ── Greenhouse ───────────────────────────────────────────────────
            "Stripe":       {"type": "greenhouse", "slug": "stripe"},
            "Airbnb":       {"type": "greenhouse", "slug": "airbnb"},
            "DoorDash":     {"type": "greenhouse", "slug": "doordashusa"},
            "Lyft":         {"type": "greenhouse", "slug": "lyft"},
            "Coinbase":     {"type": "greenhouse", "slug": "coinbase"},
            "Cloudflare":   {"type": "greenhouse", "slug": "cloudflare"},
            "Datadog":      {"type": "greenhouse", "slug": "datadog"},
            # ── Lever ────────────────────────────────────────────────────────
            "Scale AI":     {"type": "greenhouse", "slug": "scaleai"},
            "Rippling":     {"type": "indeed", "query": "rippling+software+engineer"},
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

            # ── AI Labs / Top Tech (Greenhouse) ──────────────────────────────
            "Anthropic":    {"type": "greenhouse", "slug": "anthropic"},
            "Databricks":   {"type": "greenhouse", "slug": "databricks"},
            "Snowflake":    {"type": "indeed", "query": "snowflake+product+manager"},
            "MongoDB":      {"type": "greenhouse", "slug": "mongodb"},
            "CrowdStrike":  {"type": "indeed", "query": "crowdstrike+product+manager"},
            "Confluent":    {"type": "indeed", "query": "confluent+product+manager"},
            "Palo Alto":    {"type": "indeed", "query": "paloalto+product+manager"},
            "ServiceNow":   {"type": "indeed", "query": "servicenow+product+manager"},

            # ── Lever ─────────────────────────────────────────────────────────
            "Palantir":     {"type": "lever", "slug": "palantir"},
            "SpaceX":       {"type": "lever", "slug": "spacex-2"},

            # ── Indeed fallback ───────────────────────────────────────────────
            "OpenAI":       {"type": "indeed", "query": "openai+software+engineer"},
            "IBM":          {"type": "indeed", "query": "ibm+software+engineer"},
            "Nvidia":       {"type": "indeed", "query": "nvidia+software+engineer"},
            "Intel":        {"type": "indeed", "query": "intel+software+engineer"},
            "Tesla":        {"type": "indeed", "query": "tesla+software+engineer"},
            "Adobe":        {"type": "indeed", "query": "adobe+software+engineer"},
            "Salesforce":   {"type": "indeed", "query": "salesforce+software+engineer"},
            "Oracle":       {"type": "indeed", "query": "oracle+software+engineer"},
            "Cisco":        {"type": "indeed", "query": "cisco+software+engineer"},
            "xAI":          {"type": "indeed", "query": "xai+elon+software+engineer"},
            "Qualcomm":     {"type": "indeed", "query": "qualcomm+software+engineer"},
            "AMD":          {"type": "indeed", "query": "amd+software+engineer"},
        },
    },
}