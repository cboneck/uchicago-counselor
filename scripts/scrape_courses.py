"""Run the UChicago course catalog scraper."""

import sys
sys.path.insert(0, "backend")

from app.models.database import SessionLocal, init_db
from app.scrapers.course_scraper import scrape_all

if __name__ == "__main__":
    init_db()
    db = SessionLocal()
    try:
        scrape_all(db)
    finally:
        db.close()
