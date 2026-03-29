"""Build ChromaDB embeddings from scraped data."""

import sys
sys.path.insert(0, "backend")

from app.models.database import SessionLocal, init_db, Course, RedditPost, RedditComment, CareerListing
from app.rag.embeddings import get_chroma_client, init_collections
from app.rag.chunker import chunk_course, chunk_reddit_post, chunk_text

if __name__ == "__main__":
    init_db()
    db = SessionLocal()
    client = get_chroma_client()
    collections = init_collections(client)

    # Index courses
    print("Indexing courses...")
    courses = db.query(Course).all()
    for course in courses:
        text = chunk_course({
            "dept": course.dept,
            "number": course.number,
            "title": course.title,
            "description": course.description or "",
            "prerequisites": course.prerequisites or "",
            "instructors": course.instructors or "",
            "quarters": course.quarters or "",
        })
        collections["course_descriptions"].add(
            documents=[text],
            metadatas=[{"dept": course.dept, "number": course.number, "course_id": course.id}],
            ids=[f"course_{course.id}"],
        )
    print(f"  Indexed {len(courses)} courses")

    # Index Reddit posts
    print("Indexing Reddit feedback...")
    posts = db.query(RedditPost).all()
    count = 0
    for post in posts:
        comments = db.query(RedditComment).filter_by(post_id=post.id).all()
        chunks = chunk_reddit_post(
            {"subreddit": post.subreddit, "title": post.title, "body": post.body or ""},
            [{"body": c.body, "score": c.score} for c in comments],
        )
        for i, chunk in enumerate(chunks):
            collections["reddit_feedback"].add(
                documents=[chunk],
                metadatas=[{"post_id": post.id, "subreddit": post.subreddit}],
                ids=[f"reddit_{post.id}_{i}"],
            )
            count += 1
    print(f"  Indexed {count} Reddit chunks")

    # Index career listings
    print("Indexing career info...")
    listings = db.query(CareerListing).all()
    for listing in listings:
        text = f"{listing.title}\n{listing.description or ''}\nEmployer: {listing.employer or 'N/A'}"
        collections["career_info"].add(
            documents=[text],
            metadatas=[{"type": listing.type or "", "listing_id": listing.id}],
            ids=[f"career_{listing.id}"],
        )
    print(f"  Indexed {len(listings)} career listings")

    db.close()
    print("Indexing complete!")
