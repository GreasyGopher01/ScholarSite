# ScholarSite Opportunity Scraper v3

Crawls **11 real source aggregator sites** (the same sources that produced
`List_of_opportunities.xlsx`), extracts opportunities, and upserts into
**MongoDB Atlas** as deltas (only new or changed records are written).

## Source Sites Scraped

| # | Source | Pages |
|---|--------|-------|
| 1 | **CollegeVine Blog** | 22 list pages (internships, scholarships, summer programs, STEM, leadership…) |
| 2 | **Scholarships360** | 26 pages (seniors, juniors, freshmen, STEM, minority, arts, nursing…) |
| 3 | **Niche** | 9 category pages (merit, need-based, STEM, arts, first-gen…) |
| 4 | **GoingMerry** | 13 blog pages (scholarships, internships, grants, STEM, minority…) |
| 5 | **Bold.org** | 14 category pages (HS, STEM, minority, women, arts, need-based…) |
| 6 | **Fastweb** | 13 article pages (seniors, STEM, women, minority, community service…) |
| 7 | **College Transitions** | 11 pages (summer, internships, competitions, research, fellowships…) |
| 8 | **PrepScholar Blog** | 11 pages (summer, research, scholarships, competitions, grants…) |
| 9 | **ScholarLaunch** | 6 pages (spring/summer programs, internships, scholarships…) |
| 10 | **OpportunityDesk** | 6 category pages (scholarships, internships, fellowships, grants…) |
| 11 | **Idealist** | 2 pages (HS internships, volunteer opportunities) |

## MongoDB Schema

```json
{
  "_id":         "sha1(title+url)",
  "title":       "string",
  "category":    "Scholarship | Training Programs | Internship | Grants | Fellowship | Competition | Bootcamp | Apprenticeship | Courses",
  "tags":        ["array", "of", "strings"],
  "description": "string",
  "rating":      null,
  "state":       "National | Alabama | ...",
  "cost":        "Free | Paid | $500 | Varies",
  "web_link":    "https://direct-opportunity-url.com",
  "deadline":    "Rolling | Jan 15, 2026 | Varies",
  "source_url":  "https://blog.collegevine.com/internships-for-high-school-students",
  "source_name": "CollegeVine Blog",
  "scraped_at":  "2026-04-17T06:00:00Z",
  "updated_at":  "2026-04-17T06:00:00Z"
}
```

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your MongoDB Atlas URI and email settings

# 3. Run once
python scraper.py

# 4. Run on weekly schedule
python scraper.py --schedule
```

## Email Log Delivery

Add these env vars to `batch/.env` if you want the scraper run logs emailed after every execution:

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-smtp-user
SMTP_PASSWORD=your-smtp-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
EMAIL_FROM=alerts@example.com
EMAIL_TO=you@example.com,admin@example.com
```
## Windows Scheduled Task

Use the included PowerShell helper to create a Windows Scheduled Task for the scraper.

```powershell
cd batch
powershell -ExecutionPolicy Bypass -File register-scraper-task.ps1
```

The default task runs weekly on Monday at 6:00 AM.

To customize the schedule:

```powershell
# Run every hour for 24 hours starting at midnight
powershell -ExecutionPolicy Bypass -File register-scraper-task.ps1 -Frequency Hourly -At 12:00AM -IntervalMinutes 60 -RepetitionDurationHours 24

# Run every 2 hours daily starting at midnight
powershell -ExecutionPolicy Bypass -File register-scraper-task.ps1 -Frequency Daily -At 12:00AM -IntervalMinutes 120 -RepetitionDurationHours 24

# Run every hour on Monday and Friday starting at 4:00 AM
powershell -ExecutionPolicy Bypass -File register-scraper-task.ps1 -Frequency Weekly -DaysOfWeek Monday,Friday -At 04:00AM -IntervalMinutes 60 -RepetitionDurationHours 24
```

## Deploy to Render (recommended — free cron)

1. Push this folder to a GitHub repo
2. Go to [dashboard.render.com](https://dashboard.render.com) → **New → Cron Job**
3. Connect your repo → Render auto-reads `render.yaml`
4. Set `MONGODB_URI` as a secret env var in the Render dashboard
5. Done — runs every Monday at 6 AM UTC

## Deploy to Vercel

1. `npm i -g vercel && vercel login`
2. Set env vars: `vercel env add MONGODB_URI` and `vercel env add CRON_SECRET`
3. `vercel deploy`
4. Cron is configured in `vercel.json` (runs every Monday at 6 AM UTC)

## Delta Logic

- Each opportunity gets a stable `_id = sha1(title + web_link)`
- `$setOnInsert` sets `scraped_at` only on first insert
- `$set` always updates content fields + `updated_at`
- Re-running never creates duplicates — only writes what changed
- Bulk-written in batches of 500 for efficiency

## Adding New Sources

Add a scraper function and register it in the `SOURCES` list at the bottom
of `scraper.py`. Each scraper returns `list[dict]` with the schema above.
