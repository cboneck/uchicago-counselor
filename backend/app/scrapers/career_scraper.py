"""
Scraper for UChicago Career Advancement resources.
Target: careeradvancement.uchicago.edu
"""

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models.database import CareerListing

BASE_URL = "https://careeradvancement.uchicago.edu"


def scrape_resources() -> list[dict]:
    """Scrape career resources and listings."""
    listings = []

    # Scrape career resources pages
    resource_urls = [
        f"{BASE_URL}/jobs-internships/",
        f"{BASE_URL}/graduate-professional-school/",
    ]

    for url in resource_urls:
        try:
            resp = requests.get(url, timeout=10)
            soup = BeautifulSoup(resp.text, "lxml")

            for article in soup.select("article, .listing, .resource-item"):
                title_el = article.select_one("h2, h3, .title")
                desc_el = article.select_one("p, .description, .summary")
                link_el = article.select_one("a")

                if not title_el:
                    continue

                listing_type = "job" if "jobs" in url else "grad_school"

                listings.append({
                    "title": title_el.get_text(strip=True),
                    "description": desc_el.get_text(strip=True) if desc_el else "",
                    "url": link_el.get("href", "") if link_el else "",
                    "type": listing_type,
                    "employer": "",
                })
        except requests.RequestException as e:
            print(f"Error scraping {url}: {e}")

    return listings


def save_listings(db: Session, listings: list[dict]):
    """Save career listings to the database."""
    for listing in listings:
        db.add(CareerListing(**listing))
    db.commit()


def scrape_all(db: Session):
    """Run the full career data scrape."""
    print("Scraping career resources...")
    listings = scrape_resources()
    print(f"Found {len(listings)} career resources")
    save_listings(db, listings)
    print("Career scraping complete!")
