"""
scraper.py  –  ScholarSite Opportunity Scraper v3
==================================================
Crawls SOURCE aggregator pages (CollegeVine blog, Scholarships360,
Niche, Fastweb, GoingMerry, Bold.org, College Transitions, PrepScholar,
OpportunityDesk, etc.) — the same sites that produced the
List_of_opportunities.xlsx — extracts every opportunity found, and
UPSERTS into MongoDB (delta only: new or changed records).

Usage
-----
  python scraper.py              # run once
  python scraper.py --schedule   # run weekly

Env vars
--------
  MONGODB_URI      mongodb+srv://user:pass@cluster.mongodb.net/
  DB_NAME          scholarsite          (default)
  COLLECTION_NAME  opportunities        (default)
  LOG_LEVEL        INFO                 (default)
"""

import hashlib
import logging
import os
import re
import sys
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
load_dotenv(dotenv_path=Path(__file__).with_name(".env"))
MONGODB_URI     = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DB_NAME         = os.getenv("DB_NAME", "scholarsite")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "opportunities")
CRAWL_DELAY     = 1.2   # seconds between requests
TIMEOUT         = 15

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Boilerplate headings to skip on all pages
SKIP_HEADINGS = {
    "how to", "tips for", "why", "what is", "faq", "faqs",
    "conclusion", "summary", "overview", "table of contents",
    "bottom line", "key takeaway", "about", "introduction",
    "related article", "see also", "read more", "share",
    "subscribe", "follow", "comment", "more resource",
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def make_id(title: str, url: str) -> str:
    raw = f"{title.strip().lower()}|{url.strip().lower()}"
    return hashlib.sha1(raw.encode()).hexdigest()


def fetch(url: str) -> BeautifulSoup | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        log.warning("  Fetch failed [%s]: %s", url, e)
        return None


def clean(text: str | None, max_len: int = 500) -> str:
    if not text:
        return ""
    return " ".join(text.split())[:max_len]


def normalize_title(title: str) -> str:
    title = title.strip()
    title = re.sub(r"^\s*\d+\s*[\.\)\-:]*\s*", "", title)
    return title


def is_skip_heading(title: str) -> bool:
    t = title.lower()
    return any(t.startswith(s) or t == s for s in SKIP_HEADINGS)


def infer_category(title: str, text: str) -> str:
    t = (title + " " + text).lower()
    if any(w in t for w in ["scholarship", " award", " prize"]):
        return "Scholarship"
    if any(w in t for w in ["internship", "intern "]):
        return "Internship"
    if any(w in t for w in [" grant", "funding", " fund "]):
        return "Grants"
    if any(w in t for w in ["fellowship", "fellow "]):
        return "Fellowship"
    if any(w in t for w in ["competition", "contest", "olympiad", " challenge"]):
        return "Competition"
    if any(w in t for w in ["bootcamp", "boot camp"]):
        return "Bootcamp"
    if any(w in t for w in ["apprenticeship"]):
        return "Apprenticeship"
    if any(w in t for w in ["course", "mooc", "online class"]):
        return "Courses"
    return "Training Programs"


def infer_cost(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["free", "no cost", "no fee", "at no cost"]):
        return "Free"
    if any(w in t for w in ["paid", "stipend", "salary", "earn "]):
        return "Paid"
    m = re.search(r"\$[\d,]+", text)
    return m.group() if m else "Varies"


def infer_deadline(text: str) -> str:
    patterns = [
        r"deadline[:\s]+([A-Z][a-z]+ \d{1,2},?\s*\d{4})",
        r"apply by[:\s]+([A-Z][a-z]+ \d{1,2},?\s*\d{4})",
        r"due[:\s]+([A-Z][a-z]+ \d{1,2},?\s*\d{4})",
        r"applications?\s+(?:close[sd]?|due)[:\s]+([A-Z][a-z]+ \d{1,2},?\s*\d{4})",
        r"(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+\d{1,2},?\s*20\d{2}",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return (m.group(1) if m.lastindex else m.group()).strip()
    return "Rolling" if "rolling" in text.lower() else "Varies"


def resolve_link(href: str, base_url: str, source_domain: str) -> str:
    """Return the opportunity's direct URL, falling back to base_url."""
    if not href:
        return base_url
    if href.startswith("http"):
        # Only use external links (not back to the source site)
        if source_domain not in href:
            return href
        return base_url
    if href.startswith("/"):
        parsed = urlparse(base_url)
        return f"{parsed.scheme}://{parsed.netloc}{href}"
    return base_url


def build_record(
    title: str,
    description: str,
    web_link: str,
    source_url: str,
    source_name: str,
    extra_text: str = "",
    state: str = "National",
) -> dict:
    title = normalize_title(title)
    combined = description + " " + extra_text
    now = datetime.now(timezone.utc)
    record_id = make_id(title, web_link)
    return {
        "_id":         record_id,
        "id":          record_id,
        "title":       clean(title, 200),
        "category":    infer_category(title, combined),
        "tags":        [],
        "description": clean(description),
        "rating":      None,
        "state":       state,
        "location":    state,
        "nationality": state,
        "cost":        infer_cost(combined),
        "web_link":    web_link,
        "sourceLink":  web_link,
        "deadline":    infer_deadline(combined),
        "source_url":  source_url,
        "source_name": source_name,
        "scraped_at":  now,
        "createdTS":   now,
        "updated_at":  now,
    }


def extract_from_headings(
    soup: BeautifulSoup,
    source_url: str,
    source_name: str,
    max_desc_paras: int = 3,
) -> list[dict]:
    """Generic heading-based extractor used by most blog sources."""
    source_domain = urlparse(source_url).netloc
    records = []
    for h in soup.find_all(["h2", "h3"]):
        title = clean(h.get_text())
        if len(title) < 8 or len(title) > 200:
            continue
        if is_skip_heading(title):
            continue

        desc_parts, extra_text = [], ""
        for sib in h.find_next_siblings():
            if sib.name in ("h2", "h3"):
                break
            if sib.name in ("p", "li"):
                t = clean(sib.get_text())
                if t:
                    desc_parts.append(t)
            if len(desc_parts) >= max_desc_paras:
                break
        description = " ".join(desc_parts)

        link_tag = h.find("a", href=True) or h.find_next("a", href=True)
        href = link_tag["href"] if link_tag else ""
        web_link = resolve_link(href, source_url, source_domain)

        records.append(build_record(
            title=title,
            description=description,
            web_link=web_link,
            source_url=source_url,
            source_name=source_name,
        ))
    return records


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE SCRAPERS
# ─────────────────────────────────────────────────────────────────────────────

# ── 1. CollegeVine Blog ───────────────────────────────────────────────────────
COLLEGEVINE_PAGES = [
    "https://blog.collegevine.com/most-prestigious-summer-programs-for-high-school-students",
    "https://blog.collegevine.com/14-awesome-internships-for-high-school-students",
    "https://blog.collegevine.com/research-opportunities-high-school",
    "https://blog.collegevine.com/best-scholarships-for-high-school-seniors",
    "https://blog.collegevine.com/scholarships-for-low-income-students",
    "https://blog.collegevine.com/remote-internships-for-high-school-students",
    "https://blog.collegevine.com/business-internships-for-high-school-students",
    "https://blog.collegevine.com/high-school-film-internships-summer-programs",
    "https://blog.collegevine.com/high-school-internships-los-angeles",
    "https://blog.collegevine.com/high-school-internships-san-jose",
    "https://blog.collegevine.com/high-school-internships-miami",
    "https://blog.collegevine.com/high-school-summer-programs",
    "https://blog.collegevine.com/free-summer-programs-for-high-school-students",
    "https://blog.collegevine.com/stem-summer-programs-for-high-school",
    "https://blog.collegevine.com/leadership-programs-for-high-school-students",
    "https://blog.collegevine.com/fellowships-for-high-school-students",
    "https://blog.collegevine.com/grants-for-high-school-students",
    "https://blog.collegevine.com/extracurricular-activities-for-high-school-students",
    "https://blog.collegevine.com/high-school-summer-programs-new-york",
    "https://blog.collegevine.com/math-summer-programs",
    "https://blog.collegevine.com/online-summer-programs-for-high-school-students",
    "https://blog.collegevine.com/25-summer-leadership-programs-for-high-school-students",
]


def scrape_collegevine() -> list[dict]:
    results = []
    for url in COLLEGEVINE_PAGES:
        soup = fetch(url)
        if soup:
            recs = extract_from_headings(soup, url, "CollegeVine Blog")
            log.info("  CollegeVine /%s → %d", url.split("/")[-1][:45], len(recs))
            results.extend(recs)
        time.sleep(CRAWL_DELAY)
    return results


# ── 2. Scholarships360 ────────────────────────────────────────────────────────
SCHOLARSHIPS360_PAGES = [
    "https://scholarships360.org/scholarships/scholarships-for-high-school-seniors/",
    "https://scholarships360.org/scholarships/top-scholarships-for-high-school-juniors/",
    "https://scholarships360.org/scholarships/top-scholarships-for-high-school-freshman/",
    "https://scholarships360.org/scholarships/summer-scholarships/",
    "https://scholarships360.org/careers/internship-for-high-school-students/",
    "https://scholarships360.org/college-admissions/summer-programs-for-high-school-students/",
    "https://scholarships360.org/scholarships/stem-scholarships/",
    "https://scholarships360.org/scholarships/scholarships-for-women/",
    "https://scholarships360.org/scholarships/scholarships-for-minority-students/",
    "https://scholarships360.org/scholarships/need-based-scholarships/",
    "https://scholarships360.org/scholarships/merit-scholarships/",
    "https://scholarships360.org/scholarships/art-scholarships/",
    "https://scholarships360.org/scholarships/creative-writing-scholarships/",
    "https://scholarships360.org/careers/medical-internships-for-high-school-students/",
    "https://scholarships360.org/careers/engineering-internships-for-high-school-students/",
    "https://scholarships360.org/scholarships/community-service-scholarships/",
    "https://scholarships360.org/scholarships/leadership-scholarships/",
    "https://scholarships360.org/scholarships/stem-scholarships-for-high-school/",
    "https://scholarships360.org/scholarships/scholarships-for-black-students/",
    "https://scholarships360.org/scholarships/scholarships-for-hispanic-students/",
    "https://scholarships360.org/scholarships/scholarships-for-asian-students/",
    "https://scholarships360.org/scholarships/scholarships-for-native-american-students/",
    "https://scholarships360.org/scholarships/athletic-scholarships/",
    "https://scholarships360.org/scholarships/nursing-scholarships/",
    "https://scholarships360.org/scholarships/music-scholarships/",
    "https://scholarships360.org/scholarships/environmental-scholarships/",
]


def scrape_scholarships360() -> list[dict]:
    results = []
    for url in SCHOLARSHIPS360_PAGES:
        soup = fetch(url)
        if soup:
            recs = extract_from_headings(soup, url, "Scholarships360")
            log.info("  Scholarships360 /%s → %d", url.split("/")[-2][:45], len(recs))
            results.extend(recs)
        time.sleep(CRAWL_DELAY)
    return results


# ── 3. Niche ──────────────────────────────────────────────────────────────────
NICHE_PAGES = [
    "https://www.niche.com/colleges/scholarships/",
    "https://www.niche.com/colleges/scholarships/type/merit-based/",
    "https://www.niche.com/colleges/scholarships/type/need-based/",
    "https://www.niche.com/colleges/scholarships/type/stem/",
    "https://www.niche.com/colleges/scholarships/type/arts/",
    "https://www.niche.com/colleges/scholarships/type/community-service/",
    "https://www.niche.com/colleges/scholarships/type/first-generation/",
    "https://www.niche.com/colleges/scholarships/type/athletic/",
    "https://www.niche.com/colleges/scholarships/type/international/",
]


def scrape_niche() -> list[dict]:
    results = []
    source_domain = "niche.com"
    for url in NICHE_PAGES:
        soup = fetch(url)
        if not soup:
            time.sleep(CRAWL_DELAY)
            continue
        recs = []
        # Niche renders scholarship cards
        cards = (
            soup.find_all(attrs={"data-testid": re.compile("scholarship", re.I)}) or
            soup.find_all(class_=re.compile(r"card|scholarship-card|listing", re.I))
        )
        if not cards:
            # Fallback: article tags
            cards = soup.find_all("article")
        for card in cards:
            title_tag = card.find(["h2", "h3", "h4", "strong"])
            if not title_tag:
                continue
            title = clean(title_tag.get_text())
            if len(title) < 5 or len(title) > 200:
                continue
            desc_tag = card.find("p")
            description = clean(desc_tag.get_text()) if desc_tag else ""
            link_tag = card.find("a", href=True)
            href = link_tag["href"] if link_tag else ""
            web_link = resolve_link(href, url, source_domain)
            recs.append(build_record(
                title=title,
                description=description,
                web_link=web_link,
                source_url=url,
                source_name="Niche",
                extra_text=card.get_text(),
            ))
        log.info("  Niche /%s → %d", url.split("/")[-2][:45], len(recs))
        results.extend(recs)
        time.sleep(CRAWL_DELAY)
    return results


# ── 4. GoingMerry ─────────────────────────────────────────────────────────────
GOINGMERRY_PAGES = [
    "https://www.goingmerry.com/blog/scholarships-for-high-school-students/",
    "https://www.goingmerry.com/blog/internships-for-high-school-students/",
    "https://www.goingmerry.com/blog/grants-for-high-school-students/",
    "https://www.goingmerry.com/blog/summer-programs-for-high-school-students/",
    "https://www.goingmerry.com/blog/stem-scholarships-for-high-school-students/",
    "https://www.goingmerry.com/blog/community-service-scholarships/",
    "https://www.goingmerry.com/blog/scholarships-for-women-in-stem/",
    "https://www.goingmerry.com/blog/minority-scholarships/",
    "https://www.goingmerry.com/blog/merit-scholarships-for-high-school-students/",
    "https://www.goingmerry.com/blog/leadership-scholarships/",
    "https://www.goingmerry.com/blog/arts-scholarships/",
    "https://www.goingmerry.com/blog/music-scholarships/",
    "https://www.goingmerry.com/blog/environmental-scholarships/",
]


def scrape_goingmerry() -> list[dict]:
    results = []
    for url in GOINGMERRY_PAGES:
        soup = fetch(url)
        if soup:
            recs = extract_from_headings(soup, url, "GoingMerry")
            log.info("  GoingMerry /%s → %d", url.split("/")[-2][:45], len(recs))
            results.extend(recs)
        time.sleep(CRAWL_DELAY)
    return results


# ── 5. Bold.org ───────────────────────────────────────────────────────────────
BOLDORG_PAGES = [
    "https://bold.org/scholarships/by-year/high-school/",
    "https://bold.org/scholarships/stem/",
    "https://bold.org/scholarships/community-service/",
    "https://bold.org/scholarships/minority/",
    "https://bold.org/scholarships/women/",
    "https://bold.org/scholarships/first-generation/",
    "https://bold.org/scholarships/arts/",
    "https://bold.org/scholarships/leadership/",
    "https://bold.org/scholarships/no-essay/",
    "https://bold.org/scholarships/need-based/",
    "https://bold.org/scholarships/merit/",
    "https://bold.org/scholarships/athletic/",
    "https://bold.org/scholarships/nursing/",
    "https://bold.org/scholarships/environmental/",
]


def scrape_boldorg() -> list[dict]:
    results = []
    source_domain = "bold.org"
    for url in BOLDORG_PAGES:
        soup = fetch(url)
        if not soup:
            time.sleep(CRAWL_DELAY)
            continue
        recs = []
        cards = soup.find_all("article") or soup.find_all(
            class_=re.compile(r"scholarship|card|listing", re.I)
        )
        for card in cards:
            title_tag = card.find(["h2", "h3", "h4"])
            if not title_tag:
                continue
            title = clean(title_tag.get_text())
            if len(title) < 5 or len(title) > 200:
                continue
            desc_tag = card.find("p")
            description = clean(desc_tag.get_text()) if desc_tag else ""
            link_tag = card.find("a", href=True)
            href = link_tag["href"] if link_tag else ""
            web_link = resolve_link(href, url, source_domain)
            recs.append(build_record(
                title=title,
                description=description,
                web_link=web_link,
                source_url=url,
                source_name="Bold.org",
                extra_text=card.get_text(),
            ))
        log.info("  Bold.org /%s → %d", url.split("/")[-2][:45], len(recs))
        results.extend(recs)
        time.sleep(CRAWL_DELAY)
    return results


# ── 6. Fastweb ────────────────────────────────────────────────────────────────
FASTWEB_PAGES = [
    "https://www.fastweb.com/college-scholarships/articles/scholarships-for-high-school-students",
    "https://www.fastweb.com/college-scholarships/articles/stem-scholarships-for-high-school-students",
    "https://www.fastweb.com/college-scholarships/articles/internships-for-high-school-students",
    "https://www.fastweb.com/college-scholarships/articles/summer-programs-for-high-school-students",
    "https://www.fastweb.com/college-scholarships/articles/scholarships-for-women-in-stem",
    "https://www.fastweb.com/college-scholarships/articles/minority-scholarships",
    "https://www.fastweb.com/college-scholarships/articles/scholarships-for-seniors",
    "https://www.fastweb.com/college-scholarships/articles/community-service-scholarships",
    "https://www.fastweb.com/college-scholarships/articles/leadership-scholarships",
    "https://www.fastweb.com/college-scholarships/articles/art-scholarships",
    "https://www.fastweb.com/college-scholarships/articles/music-scholarships",
    "https://www.fastweb.com/college-scholarships/articles/need-based-scholarships",
    "https://www.fastweb.com/college-scholarships/articles/merit-scholarships",
]


def scrape_fastweb() -> list[dict]:
    results = []
    for url in FASTWEB_PAGES:
        soup = fetch(url)
        if soup:
            recs = extract_from_headings(soup, url, "Fastweb")
            log.info("  Fastweb /%s → %d", url.split("/")[-1][:45], len(recs))
            results.extend(recs)
        time.sleep(CRAWL_DELAY)
    return results


# ── 7. College Transitions ────────────────────────────────────────────────────
COLLEGE_TRANSITIONS_PAGES = [
    "https://www.collegetransitions.com/blog/summer-programs/",
    "https://www.collegetransitions.com/blog/internships-for-high-school-students/",
    "https://www.collegetransitions.com/blog/scholarships-for-high-school-students/",
    "https://www.collegetransitions.com/blog/competitions-for-high-school-students/",
    "https://www.collegetransitions.com/blog/research-opportunities-for-high-school-students/",
    "https://www.collegetransitions.com/blog/community-service-opportunities/",
    "https://www.collegetransitions.com/blog/leadership-programs/",
    "https://www.collegetransitions.com/blog/fellowships-for-high-school-students/",
    "https://www.collegetransitions.com/blog/grants-for-high-school-students/",
    "https://www.collegetransitions.com/blog/free-summer-programs/",
    "https://www.collegetransitions.com/blog/stem-competitions-for-high-school-students/",
]


def scrape_college_transitions() -> list[dict]:
    results = []
    for url in COLLEGE_TRANSITIONS_PAGES:
        soup = fetch(url)
        if soup:
            recs = extract_from_headings(soup, url, "College Transitions")
            log.info("  College Transitions /%s → %d", url.split("/")[-2][:45], len(recs))
            results.extend(recs)
        time.sleep(CRAWL_DELAY)
    return results


# ── 8. PrepScholar Blog ───────────────────────────────────────────────────────
PREPSCHOLAR_PAGES = [
    "https://blog.prepscholar.com/best-summer-programs-for-high-school-students",
    "https://blog.prepscholar.com/internships-for-high-school-students",
    "https://blog.prepscholar.com/scholarships-for-high-school-students",
    "https://blog.prepscholar.com/summer-research-programs-for-high-school-students",
    "https://blog.prepscholar.com/stem-scholarships-for-high-school-students",
    "https://blog.prepscholar.com/college-scholarships-for-high-school-juniors",
    "https://blog.prepscholar.com/free-summer-programs-for-high-school-students",
    "https://blog.prepscholar.com/stem-internships-for-high-school-students",
    "https://blog.prepscholar.com/competitions-for-high-school-students",
    "https://blog.prepscholar.com/grants-for-high-school-students",
    "https://blog.prepscholar.com/high-school-fellowships",
]


def scrape_prepscholar() -> list[dict]:
    results = []
    for url in PREPSCHOLAR_PAGES:
        soup = fetch(url)
        if soup:
            recs = extract_from_headings(soup, url, "PrepScholar")
            log.info("  PrepScholar /%s → %d", url.split("/")[-1][:45], len(recs))
            results.extend(recs)
        time.sleep(CRAWL_DELAY)
    return results


# ── 9. ScholarLaunch ──────────────────────────────────────────────────────────
SCHOLARLAUNCH_PAGES = [
    "https://www.scholarlaunch.org/blog/best-spring-programs-for-high-school-students-in-2026",
    "https://www.scholarlaunch.org/blog/best-summer-programs-for-high-school-students",
    "https://www.scholarlaunch.org/blog/internships-for-high-school-students",
    "https://www.scholarlaunch.org/blog/scholarships-for-high-school-students",
    "https://www.scholarlaunch.org/blog/stem-programs-for-high-school-students",
    "https://www.scholarlaunch.org/blog/leadership-programs-for-high-school-students",
]


def scrape_scholarlaunch() -> list[dict]:
    results = []
    for url in SCHOLARLAUNCH_PAGES:
        soup = fetch(url)
        if soup:
            recs = extract_from_headings(soup, url, "ScholarLaunch")
            log.info("  ScholarLaunch /%s → %d", url.split("/")[-1][:45], len(recs))
            results.extend(recs)
        time.sleep(CRAWL_DELAY)
    return results


# ── 10. OpportunityDesk ───────────────────────────────────────────────────────
OPPORTUNITYDESK_PAGES = [
    "https://opportunitydesk.org/category/scholarships/",
    "https://opportunitydesk.org/category/internships/high-school-internships/",
    "https://opportunitydesk.org/category/fellowships/",
    "https://opportunitydesk.org/category/grants/",
    "https://opportunitydesk.org/category/competitions/",
    "https://opportunitydesk.org/category/programs/",
]


def scrape_opportunitydesk() -> list[dict]:
    """OpportunityDesk lists post titles as article links."""
    results = []
    source_domain = "opportunitydesk.org"
    for url in OPPORTUNITYDESK_PAGES:
        soup = fetch(url)
        if not soup:
            time.sleep(CRAWL_DELAY)
            continue
        recs = []
        # Each post = <article> with <h2><a>
        articles = soup.find_all("article")
        for art in articles:
            a_tag = art.find("a", href=True)
            h_tag = art.find(["h2", "h3"])
            if not h_tag:
                continue
            title = clean(h_tag.get_text())
            if len(title) < 8 or len(title) > 200:
                continue
            desc_tag = art.find("p")
            description = clean(desc_tag.get_text()) if desc_tag else ""
            href = a_tag["href"] if a_tag else ""
            web_link = resolve_link(href, url, source_domain)
            recs.append(build_record(
                title=title,
                description=description,
                web_link=web_link,
                source_url=url,
                source_name="OpportunityDesk",
                extra_text=art.get_text(),
            ))
        log.info("  OpportunityDesk /%s → %d", url.split("/")[-2][:45], len(recs))
        results.extend(recs)
        time.sleep(CRAWL_DELAY)
    return results


# ── 11. Idealist ──────────────────────────────────────────────────────────────
def scrape_idealist() -> list[dict]:
    urls = [
        "https://www.idealist.org/en/internships?q=high+school",
        "https://www.idealist.org/en/volunteer-opportunities?q=high+school",
    ]
    results = []
    source_domain = "idealist.org"
    for url in urls:
        soup = fetch(url)
        if not soup:
            time.sleep(CRAWL_DELAY)
            continue
        recs = []
        cards = soup.find_all(attrs={"data-testid": re.compile("listing", re.I)}) or []
        if not cards:
            cards = soup.find_all(class_=re.compile(r"card|listing|result", re.I))
        for card in cards:
            title_tag = card.find(["h2", "h3", "h4"])
            if not title_tag:
                continue
            title = clean(title_tag.get_text())
            if len(title) < 5:
                continue
            desc_tag = card.find("p")
            description = clean(desc_tag.get_text()) if desc_tag else ""
            link_tag = card.find("a", href=True)
            href = link_tag["href"] if link_tag else ""
            web_link = resolve_link(href, url, source_domain)
            recs.append(build_record(
                title=title,
                description=description,
                web_link=web_link,
                source_url=url,
                source_name="Idealist",
            ))
        log.info("  Idealist → %d", len(recs))
        results.extend(recs)
        time.sleep(CRAWL_DELAY)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE REGISTRY  –  add new scrapers here
# ─────────────────────────────────────────────────────────────────────────────
SOURCES = [
    ("CollegeVine Blog",    scrape_collegevine),
    ("Scholarships360",     scrape_scholarships360),
    ("Niche",               scrape_niche),
    ("GoingMerry",          scrape_goingmerry),
    ("Bold.org",            scrape_boldorg),
    ("Fastweb",             scrape_fastweb),
    ("College Transitions", scrape_college_transitions),
    ("PrepScholar",         scrape_prepscholar),
    ("ScholarLaunch",       scrape_scholarlaunch),
    ("OpportunityDesk",     scrape_opportunitydesk),
    ("Idealist",            scrape_idealist),
]


# ─────────────────────────────────────────────────────────────────────────────
# DEDUPLICATION
# ─────────────────────────────────────────────────────────────────────────────

def deduplicate(records: list[dict]) -> list[dict]:
    """Keep the longest description per _id."""
    seen: dict[str, dict] = {}
    for r in records:
        rid = r["_id"]
        if rid not in seen or len(r["description"]) > len(seen[rid]["description"]):
            seen[rid] = r
    return list(seen.values())


def quality_filter(records: list[dict]) -> list[dict]:
    bad = {
        "overview", "summary", "introduction", "conclusion",
        "how to apply", "faq", "about us", "contact", "home",
    }
    return [
        r for r in records
        if len(r["title"]) >= 8
        and r["title"].lower() not in bad
        and not r["title"].lower().startswith("how to ")
    ]


# ─────────────────────────────────────────────────────────────────────────────
# MONGODB DELTA UPSERT
# ─────────────────────────────────────────────────────────────────────────────

def get_mongo_client() -> MongoClient:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10_000)
    client.admin.command("ping")
    log.info("MongoDB connection successful: %s.%s", DB_NAME, COLLECTION_NAME)
    return client


def upsert_to_mongo(records: list[dict]) -> dict:
    """
    Upsert into MongoDB.
    - $setOnInsert: sets scraped_at only on first insert
    - $set: always updates content fields + updated_at
    Returns: {inserted, updated, unchanged, errors, total}
    """
    client = get_mongo_client()
    db  = client[DB_NAME]
    col = db[COLLECTION_NAME]

    # Indexes for fast querying
    for field in ["web_link", "source_name", "category", "state",
                  "scraped_at", "updated_at", "deadline"]:
        col.create_index(field, background=True)

    now = datetime.now(timezone.utc)
    ops = [
        UpdateOne(
            {"_id": r["_id"]},
            {
                "$setOnInsert": {
                    "scraped_at": now,
                    "createdTS":  now,
                },
                "$set": {
                    "id":          r["id"],
                    "title":       r["title"],
                    "category":    r["category"],
                    "tags":        r["tags"],
                    "description": r["description"],
                    "state":       r["state"],
                    "location":    r["location"],
                    "nationality": r["nationality"],
                    "cost":        r["cost"],
                    "deadline":    r["deadline"],
                    "web_link":    r["web_link"],
                    "sourceLink":  r["sourceLink"],
                    "source_url":  r["source_url"],
                    "source_name": r["source_name"],
                    "updated_at":  now
                },
            },
            upsert=True,
        )
        for r in records
    ]

    stats = {"inserted": 0, "updated": 0, "unchanged": 0, "errors": 0, "total": len(records)}

    BATCH = 500
    for i in range(0, len(ops), BATCH):
        try:
            res = col.bulk_write(ops[i : i + BATCH], ordered=False)
            stats["inserted"] += res.upserted_count
            stats["updated"]  += res.modified_count
        except BulkWriteError as bwe:
            stats["errors"] += len(bwe.details.get("writeErrors", []))
            log.error("BulkWriteError (partial): %s",
                      bwe.details.get("writeErrors", [])[:2])

    stats["unchanged"] = max(
        0, len(records) - stats["inserted"] - stats["updated"] - stats["errors"]
    )
    client.close()
    return stats


# ─────────────────────────────────────────────────────────────────────────────
# MAIN JOB
# ─────────────────────────────────────────────────────────────────────────────

def run_job() -> dict:
    log.info("=" * 65)
    log.info("ScholarSite Scraper v3  —  %s", datetime.now(timezone.utc).isoformat())
    log.info("=" * 65)

    all_records: list[dict] = []
    for name, fn in SOURCES:
        log.info("▶ %s", name)
        try:
            recs = fn()
            log.info("  ✓ %s total from %s", len(recs), name)
            all_records.extend(recs)
        except Exception as e:
            log.error("  ✗ Scraper [%s] crashed: %s", name, e)

    log.info("Raw total: %d records", len(all_records))

    unique  = deduplicate(all_records)
    log.info("After dedup: %d", len(unique))

    filtered = quality_filter(unique)
    log.info("After quality filter: %d", len(filtered))

    log.info("Upserting into MongoDB [%s.%s]...", DB_NAME, COLLECTION_NAME)
    stats = upsert_to_mongo(filtered)
    log.info(
        "✅ MongoDB → inserted: %d | updated: %d | unchanged: %d | errors: %d | total: %d",
        stats["inserted"], stats["updated"],
        stats["unchanged"], stats["errors"], stats["total"],
    )
    log.info("=" * 65)
    return stats


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="ScholarSite opportunity scraper → MongoDB (delta upsert)"
    )
    parser.add_argument(
        "--schedule", action="store_true",
        help="Run weekly on a cron schedule (uses `schedule` pkg)"
    )
    args = parser.parse_args()

    if args.schedule:
        try:
            import schedule as sched
        except ImportError:
            log.error("Install schedule: pip install schedule")
            sys.exit(1)
        log.info("Weekly job scheduled. Running immediately...")
        run_job()
        sched.every().week.do(run_job)
        while True:
            sched.run_pending()
            time.sleep(3600)
    else:
        run_job()


if __name__ == "__main__":
    main()
