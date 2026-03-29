"""
Scraper for the UChicago course catalog.
Target: catalog.uchicago.edu
"""

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models.database import Course, Major, MajorRequirement

BASE_URL = "http://collegecatalog.uchicago.edu"


def get_departments() -> list[dict]:
    """Fetch list of departments from the catalog."""
    resp = requests.get(f"{BASE_URL}/thecollege/programsofstudy/")
    soup = BeautifulSoup(resp.text, "lxml")

    departments = []
    # Department links live in the left nav menu
    nav = soup.select("ul.nav.leveltwo li a")
    for link in nav:
        href = link.get("href", "")
        name = link.get_text(strip=True)
        if name and href and href.startswith("/thecollege/") and href != "/thecollege/programsofstudy/":
            departments.append({"name": name, "url": BASE_URL + href})

    return departments


def scrape_courses_for_dept(dept_url: str, dept_name: str) -> list[dict]:
    """Scrape all courses for a given department page."""
    resp = requests.get(dept_url)
    soup = BeautifulSoup(resp.text, "lxml")

    courses = []
    for block in soup.select("div.courseblock.main"):
        title_el = block.select_one(".courseblocktitle strong")
        desc_el = block.select_one(".courseblockdesc")
        detail_el = block.select_one(".courseblockdetail")

        if not title_el:
            continue

        # Title format: "DEPT\xa012345.  Course Title.  100 Units."
        title_text = title_el.get_text(strip=True)
        # Replace non-breaking spaces with regular spaces
        title_text = title_text.replace("\xa0", " ")

        # Split on ". " to separate code, title, and units
        parts = [p.strip() for p in title_text.split(".") if p.strip()]
        if len(parts) >= 2:
            course_id = parts[0].strip()
            course_title = parts[1].strip()
            units = parts[2].strip() if len(parts) > 2 else ""
        else:
            course_id = title_text
            course_title = title_text
            units = ""

        # Split course_id into dept and number
        id_parts = course_id.split(maxsplit=1)
        dept_code = id_parts[0] if id_parts else dept_name
        number = id_parts[1] if len(id_parts) > 1 else ""

        description = desc_el.get_text(strip=True) if desc_el else ""

        # Parse prerequisites and terms from detail block
        prerequisites = ""
        quarters = ""
        instructors = ""
        if detail_el:
            detail_text = detail_el.get_text(separator="\n")
            for line in detail_text.split("\n"):
                line = line.strip()
                if line.startswith("Prerequisite(s):"):
                    prerequisites = line.replace("Prerequisite(s):", "").strip()
                elif line.startswith("Terms Offered:"):
                    quarters = line.replace("Terms Offered:", "").strip()
                elif line.startswith("Instructor(s):"):
                    instructors = line.replace("Instructor(s):", "").strip()

        courses.append({
            "dept": dept_code,
            "number": number,
            "title": course_title,
            "description": description,
            "units": units,
            "prerequisites": prerequisites or None,
            "quarters": quarters or None,
            "instructors": instructors or None,
        })

    return courses


def save_courses(db: Session, courses: list[dict]):
    """Save scraped courses to the database."""
    for c in courses:
        existing = (
            db.query(Course)
            .filter_by(dept=c["dept"], number=c["number"])
            .first()
        )
        if existing:
            existing.title = c["title"]
            existing.description = c["description"]
            existing.units = c.get("units", "")
        else:
            db.add(Course(**c))
    db.commit()


def scrape_all(db: Session):
    """Run the full course catalog scrape."""
    print("Fetching departments...")
    departments = get_departments()
    print(f"Found {len(departments)} departments")

    for dept in departments:
        print(f"Scraping: {dept['name']}...")
        courses = scrape_courses_for_dept(dept["url"], dept["name"])
        print(f"  Found {len(courses)} courses")
        save_courses(db, courses)

    print("Course scraping complete!")
