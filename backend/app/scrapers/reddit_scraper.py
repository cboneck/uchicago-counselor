"""
Reddit scraper via public JSON endpoints (no API credentials needed).
Searches for UChicago course discussions on Reddit.
"""

import re
import time
from datetime import datetime

import requests
from sqlalchemy.orm import Session

from app.models.database import RedditPost, RedditComment, CourseMention, Course

SUBREDDITS = ["uchicago"]

HEADERS = {
    "User-Agent": "uchicago-counselor/1.0 (educational project)",
}

# Built dynamically from the course database
_dept_codes: set[str] | None = None


def _load_dept_codes(db: Session) -> set[str]:
    """Load valid department codes from the courses table."""
    global _dept_codes
    if _dept_codes is None:
        rows = db.query(Course.dept).distinct().all()
        _dept_codes = {r[0] for r in rows}
    return _dept_codes


def build_course_pattern(dept_codes: set[str]) -> re.Pattern:
    """Build a regex that matches real UChicago course codes like CMSC 15100."""
    depts = "|".join(sorted(dept_codes))
    return re.compile(rf"\b({depts})\s*(\d{{4,5}})\b", re.IGNORECASE)


def extract_course_mentions(text: str, pattern: re.Pattern) -> list[tuple[str, str]]:
    """Extract course IDs from text. Returns deduplicated list of (dept, number) tuples."""
    return list({(dept.upper(), num) for dept, num in pattern.findall(text or "")})


def search_reddit_json(
    query: str,
    subreddit: str,
    course_pattern: re.Pattern,
    time_filter: str = "month",
    limit: int = 25,
) -> list[dict]:
    """
    Search Reddit using the public JSON endpoint.
    Only returns posts with course code mentions in title or body.
    """
    url = f"https://www.reddit.com/r/{subreddit}/search.json"
    params = {
        "q": query,
        "restrict_sr": "on",
        "sort": "new",
        "t": time_filter,
        "limit": str(limit),
    }

    posts = []
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        if resp.status_code == 429:
            print(f"    Rate limited, waiting 10s...")
            time.sleep(10)
            resp = requests.get(url, params=params, headers=HEADERS, timeout=15)

        if resp.status_code != 200:
            print(f"    Search returned status {resp.status_code}")
            return posts

        data = resp.json()
        children = data.get("data", {}).get("children", [])

        for child in children:
            d = child.get("data", {})
            full_text = f"{d.get('title', '')} {d.get('selftext', '')}"
            mentions = extract_course_mentions(full_text, course_pattern)

            if not mentions:
                continue

            posts.append({
                "id": d.get("id", ""),
                "subreddit": subreddit,
                "title": d.get("title", ""),
                "body": d.get("selftext", ""),
                "score": d.get("score", 0),
                "date": d.get("created_utc", 0),
                "url": f"https://reddit.com{d.get('permalink', '')}",
                "mentions": mentions,
                "comments": [],
            })

    except requests.RequestException as e:
        print(f"    Error searching Reddit: {e}")

    return posts


def fetch_post_comments(permalink: str, limit: int = 20) -> list[dict]:
    """Fetch comments for a specific Reddit post via the JSON endpoint."""
    comments = []
    # Convert permalink to JSON URL
    url = permalink.rstrip("/") + ".json"
    if not url.startswith("http"):
        url = f"https://www.reddit.com{url}"

    try:
        resp = requests.get(url, headers=HEADERS, params={"limit": str(limit)}, timeout=15)
        if resp.status_code != 200:
            return comments

        data = resp.json()
        if len(data) < 2:
            return comments

        # Second element in the array contains comments
        comment_listing = data[1].get("data", {}).get("children", [])
        for child in comment_listing:
            if child.get("kind") != "t1":
                continue
            d = child.get("data", {})
            comment_id = d.get("id", "")
            body = d.get("body", "")
            if comment_id and body:
                comments.append({
                    "id": comment_id,
                    "body": body,
                    "score": d.get("score", 0),
                    "date": d.get("created_utc", 0),
                })

    except (requests.RequestException, ValueError) as e:
        print(f"    Error fetching comments: {e}")

    return comments[:limit]


def save_posts(db: Session, posts: list[dict]) -> int:
    """Save scraped Reddit posts and comments to the database."""
    saved = 0
    for p in posts:
        existing = db.query(RedditPost).filter_by(id=p["id"]).first()
        if existing:
            continue

        post = RedditPost(
            id=p["id"],
            subreddit=p["subreddit"],
            title=p["title"],
            body=p["body"],
            score=p["score"],
            date=datetime.utcfromtimestamp(p["date"]),
            url=p["url"],
        )
        db.add(post)

        for c in p["comments"]:
            comment = RedditComment(
                id=c["id"],
                post_id=p["id"],
                body=c["body"],
                score=c["score"],
                date=datetime.utcfromtimestamp(c["date"]),
            )
            db.add(comment)

        # Save course mentions linked to actual courses in DB
        for dept, number in p.get("mentions", []):
            course = db.query(Course).filter_by(dept=dept, number=number).first()
            mention = CourseMention(
                reddit_id=p["id"],
                course_id=course.id if course else None,
                sentiment=None,
            )
            db.add(mention)

        saved += 1

    db.commit()
    return saved


def scrape_all(db: Session, time_filter: str = "month", limit: int = 25):
    """
    Scrape Reddit for posts mentioning UChicago courses.
    Uses public JSON endpoints (no API credentials needed).

    time_filter: 'day', 'week', 'month', 'year', 'all'
    """
    dept_codes = _load_dept_codes(db)
    course_pattern = build_course_pattern(dept_codes)

    # Search for popular department codes and course-related terms
    search_queries = [
        "CMSC",
        "ECON",
        "MATH",
        "PHYS",
        "STAT",
        "CHEM",
        "BIOS",
        "PSYC",
        "HIST",
        "POLI",
        "course review",
        "class difficulty",
        "professor recommendation",
        "course load",
    ]

    total_saved = 0
    seen_ids = set()

    for sub in SUBREDDITS:
        print(f"Scraping r/{sub} (time filter: {time_filter})...\n")

        for query in search_queries:
            print(f"  Searching: '{query}'...")
            posts = search_reddit_json(query, sub, course_pattern, time_filter=time_filter, limit=limit)

            # Deduplicate across searches
            new_posts = [p for p in posts if p["id"] not in seen_ids]
            seen_ids.update(p["id"] for p in new_posts)

            if not new_posts:
                print(f"    No new posts with course mentions")
            else:
                for p in new_posts:
                    courses = ", ".join(f"{d} {n}" for d, n in p["mentions"])
                    print(f"    [{p['score']}] {p['title'][:70]}  ({courses})")

                # Fetch comments for each post
                for i, post in enumerate(new_posts):
                    post["comments"] = fetch_post_comments(post["url"])
                    print(f"    -> {len(post['comments'])} comments fetched")
                    time.sleep(1)  # Be polite

                saved = save_posts(db, new_posts)
                total_saved += saved

            time.sleep(2)  # Delay between searches

    print(f"\nReddit scraping complete! {total_saved} total new posts saved.")
    print(f"Total unique posts found: {len(seen_ids)}")
