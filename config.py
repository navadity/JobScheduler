# ============================================================
#  JOB ALERT CONFIG  —  Edit everything in this file
# ============================================================
#
#  HOW PROFILES WORK
#  ─────────────────
#  Each entry in PROFILES is an independent alert pipeline:
#    - Its own target roles & exclude keywords
#    - Its own company list (with ATS type + slug/query)
#    - Its own destination email (and optional Telegram chat)
#
#  Add as many profiles as you want. Each runs separately and
#  sends alerts only to the right person.
# ============================================================

PROFILES = {

    # ══════════════════════════════════════════════════════════
    #  PROFILE 1 — Product Manager
    # ══════════════════════════════════════════════════════════
    "product_manager": {

        "label": "Product Manager",          # Used in email subject lines
        "active": True,                      # Set False to pause this profile

        # ── Roles to match (case-insensitive substring match on job title)
        "target_roles": [
            "Senior Product Manager",
            "Sr. Product Manager",
            "Sr Product Manager",
            "Principal Product Manager",
            "Group Product Manager",
            "Director of Product",
            "Director, Product",
            "Head of Product",
            "Staff Product Manager",
            "Product Lead",
        ],

        # ── Job titles containing any of these are skipped
        "exclude_keywords": [
            "intern",
            "internship",
            "junior",
            "associate product manager",
            "APM",
            "entry level",
            "contract",
        ],

        # ── Where alerts go for this profile
        "notify_email": "pmhritvik@gmail.com",

        # ── Companies to watch
        "companies": {

            # BIG TECH — use Indeed RSS (they have their own ATS)
            "Amazon / AWS": {
                "type": "indeed",
                "query": "amazon+senior+product+manager",
            },
            "Microsoft": {
                "type": "indeed",
                "query": "microsoft+senior+product+manager",
            },
            "Google": {
                "type": "indeed",
                "query": "google+senior+product+manager",
            },
            "Meta": {
                "type": "indeed",
                "query": "meta+facebook+senior+product+manager",
            },
            "Apple": {
                "type": "indeed",
                "query": "apple+senior+product+manager",
            },
            "LinkedIn": {
                "type": "indeed",
                "query": "linkedin+senior+product+manager",
            },

            # GREENHOUSE ATS
            "Airbnb":      {"type": "greenhouse", "slug": "airbnb"},
            "Stripe":      {"type": "greenhouse", "slug": "stripe"},
            "Lyft":        {"type": "greenhouse", "slug": "lyft"},
            "Shopify":     {"type": "greenhouse", "slug": "shopify"},
            "Figma":       {"type": "greenhouse", "slug": "figma"},
            "Notion":      {"type": "greenhouse", "slug": "notion"},
            "Discord":     {"type": "greenhouse", "slug": "discord"},
            "Coinbase":    {"type": "greenhouse", "slug": "coinbase"},
            "DoorDash":    {"type": "greenhouse", "slug": "doordash"},
            "Databricks":  {"type": "greenhouse", "slug": "databricks"},
            "Snowflake":   {"type": "greenhouse", "slug": "snowflake"},
            "Salesforce":  {"type": "greenhouse", "slug": "salesforce"},
            "Atlassian":   {"type": "greenhouse", "slug": "atlassian"},
            "Dropbox":     {"type": "greenhouse", "slug": "dropbox"},

            # LEVER ATS
            "Netflix":   {"type": "lever", "slug": "netflix"},
            "Uber":      {"type": "lever", "slug": "uber"},
            "Zillow":    {"type": "lever", "slug": "zillow"},
            "Expedia":   {"type": "lever", "slug": "expedia"},
            "Palantir":  {"type": "lever", "slug": "palantir"},
        },
    },

    # ══════════════════════════════════════════════════════════
    #  PROFILE 2 — SDE 2 / Software Engineer II
    # ══════════════════════════════════════════════════════════
    "sde2": {

        "label": "SDE 2",
        "active": True,

        # ── Roles to match
        "target_roles": [
            "Software Development Engineer II",
            "Software Development Engineer 2",
            "SDE II",
            "SDE 2",
            "Software Engineer II",
            "Software Engineer 2",
            "SWE II",
            "SWE 2",
            "Software Engineer, L4",
            "Software Engineer L4",
            "Software Engineer (L4)",
            "Senior Software Engineer",
            "Sr. Software Engineer",
            "Sr Software Engineer",
            "Backend Engineer II",
            "Frontend Engineer II",
            "Full Stack Engineer II",
        ],

        # ── Job titles containing any of these are skipped
        "exclude_keywords": [
            "intern",
            "internship",
            "principal",
            "staff",
            "senior staff",
            "distinguished",
            "director",
            "manager",
            "L5", "L6",
            "SDE III", "SDE 3",
            "Software Engineer III",
            "Software Engineer 3",
            "entry level",
            "new grad",
            "university",
            "contract",
        ],

        # ── Where alerts go for this profile
        "notify_email": "navadityagaur@gmail.com",

        # ── Companies to watch
        "companies": {

            # BIG TECH
            "Amazon / AWS": {
                "type": "indeed",
                "query": "amazon+software+development+engineer+II",
            },
            "Microsoft": {
                "type": "indeed",
                "query": "microsoft+software+engineer+II+SDE",
            },
            "Google": {
                "type": "indeed",
                "query": "google+software+engineer+L4",
            },
            "Meta": {
                "type": "indeed",
                "query": "meta+software+engineer+E4+E5",
            },
            "Apple": {
                "type": "indeed",
                "query": "apple+software+engineer+ICT3",
            },
            "LinkedIn": {
                "type": "indeed",
                "query": "linkedin+software+engineer+II",
            },

            # GREENHOUSE ATS
            "Airbnb":      {"type": "greenhouse", "slug": "airbnb"},
            "Stripe":      {"type": "greenhouse", "slug": "stripe"},
            "Lyft":        {"type": "greenhouse", "slug": "lyft"},
            "Shopify":     {"type": "greenhouse", "slug": "shopify"},
            "Figma":       {"type": "greenhouse", "slug": "figma"},
            "Notion":      {"type": "greenhouse", "slug": "notion"},
            "Discord":     {"type": "greenhouse", "slug": "discord"},
            "Coinbase":    {"type": "greenhouse", "slug": "coinbase"},
            "DoorDash":    {"type": "greenhouse", "slug": "doordash"},
            "Databricks":  {"type": "greenhouse", "slug": "databricks"},
            "Snowflake":   {"type": "greenhouse", "slug": "snowflake"},
            "Salesforce":  {"type": "greenhouse", "slug": "salesforce"},
            "Atlassian":   {"type": "greenhouse", "slug": "atlassian"},
            "Dropbox":     {"type": "greenhouse", "slug": "dropbox"},

            # LEVER ATS
            "Netflix":   {"type": "lever", "slug": "netflix"},
            "Uber":      {"type": "lever", "slug": "uber"},
            "Zillow":    {"type": "lever", "slug": "zillow"},
            "Expedia":   {"type": "lever", "slug": "expedia"},
            "Palantir":  {"type": "lever", "slug": "palantir"},
        },
    },

}

# ── SHARED SETTINGS ──────────────────────────────────────────────────────────

LOCATION        = "Seattle, WA"
LOCATION_INDEED = "Seattle%2C+WA"   # URL-encoded for Indeed RSS
REMOTE_OK       = True              # Also surface remote-friendly jobs

# Gmail sender account — both profiles send FROM this one address
# Set GMAIL_USER + GMAIL_APP_PASSWORD in GitHub repo secrets
NOTIFY_GMAIL    = True

# Telegram — optional, one bot broadcasts all profiles' alerts to one chat
NOTIFY_TELEGRAM = False             # Flip to True + add secrets to enable

MAX_JOBS_PER_RUN  = 50    # Safety cap per profile per run
JOBS_AGE_DAYS     = 3     # Only surface jobs posted in the last N days (Indeed)
SEND_EMPTY_DIGEST = False  # Send email even when 0 new jobs found

SEEN_JOBS_FILE = "seen_jobs.json"
MAX_SEEN_JOBS  = 10000    # Trim oldest entries beyond this (across all profiles)
