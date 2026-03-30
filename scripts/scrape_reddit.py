"""Run the Reddit scraper."""

import sys
sys.path.insert(0, "backend")

from app.models.database import SessionLocal, init_db
from app.scrapers.reddit_scraper import scrape_all

if __name__ == "__main__":
    # Usage: python scripts/scrape_reddit.py [time_filter] [limit]
    # time_filter: day, week, month (default), year, all
    # limit: max posts per search query (default 25)
    time_filter = sys.argv[1] if len(sys.argv) > 1 else "month"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 25

    print(f"Scraping Reddit (time: {time_filter}, limit: {limit} per query)...\n")

    init_db()
    db = SessionLocal()
    try:
        scrape_all(db, time_filter=time_filter, limit=limit)
    finally:
        db.close()
