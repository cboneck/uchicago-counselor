"""
Reddit scraper using PRAW.
Targets: r/uchicago and related subreddits.
"""

import re
import praw
from sqlalchemy.orm import Session

from app.config import settings
from app.models.database import RedditPost, RedditComment, CourseMention, ProfessorMention

# Common UChicago course patterns: "CMSC 15100", "ECON 20100", "MATH 15300"
COURSE_PATTERN = re.compile(r"\b([A-Z]{3,5})\s*(\d{4,5})\b")

SUBREDDITS = ["uchicago", "uchicagoacademics"]


def create_reddit_client() -> praw.Reddit:
    """Create an authenticated Reddit client."""
    return praw.Reddit(
        client_id=settings.reddit_client_id,
        client_secret=settings.reddit_client_secret,
        user_agent=settings.reddit_user_agent,
    )


def extract_course_mentions(text: str) -> list[tuple[str, str]]:
    """Extract course IDs from text (e.g., 'CMSC 15100')."""
    return COURSE_PATTERN.findall(text or "")


def scrape_subreddit(reddit: praw.Reddit, subreddit_name: str, limit: int = 500) -> list[dict]:
    """Scrape posts and comments from a subreddit."""
    subreddit = reddit.subreddit(subreddit_name)
    posts = []

    for submission in subreddit.hot(limit=limit):
        post_data = {
            "id": submission.id,
            "subreddit": subreddit_name,
            "title": submission.title,
            "body": submission.selftext,
            "score": submission.score,
            "date": submission.created_utc,
            "url": submission.url,
            "comments": [],
        }

        # Get top-level comments
        submission.comments.replace_more(limit=0)
        for comment in submission.comments.list()[:50]:
            post_data["comments"].append({
                "id": comment.id,
                "body": comment.body,
                "score": comment.score,
                "date": comment.created_utc,
            })

        posts.append(post_data)

    return posts


def save_posts(db: Session, posts: list[dict]):
    """Save scraped Reddit posts and comments to the database."""
    from datetime import datetime

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

        # Extract and save course mentions from post and comments
        all_text = f"{p['title']} {p['body']}"
        for c in p["comments"]:
            all_text += f" {c['body']}"

        for dept, number in extract_course_mentions(all_text):
            mention = CourseMention(
                reddit_id=p["id"],
                sentiment=None,  # TODO: add sentiment analysis
            )
            db.add(mention)

    db.commit()


def scrape_all(db: Session, limit: int = 500):
    """Run the full Reddit scrape."""
    reddit = create_reddit_client()

    for sub in SUBREDDITS:
        print(f"Scraping r/{sub}...")
        posts = scrape_subreddit(reddit, sub, limit=limit)
        print(f"  Found {len(posts)} posts")
        save_posts(db, posts)

    print("Reddit scraping complete!")
