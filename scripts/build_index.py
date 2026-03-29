"""Build ChromaDB embeddings from scraped data."""

import sys
sys.path.insert(0, "backend")

from app.models.database import SessionLocal, init_db, Course, RedditPost, RedditComment, CareerListing
from app.rag.embeddings import get_chroma_client, init_collections
from app.rag.chunker import chunk_course, chunk_reddit_post, chunk_text

BATCH_SIZE = 20

if __name__ == "__main__":
    init_db()
    db = SessionLocal()
    client = get_chroma_client()
    collections = init_collections(client)

    # Index courses in batches
    print("Indexing courses...")
    courses = db.query(Course).all()
    docs, metas, ids = [], [], []

    for i, course in enumerate(courses):
        text = chunk_course({
            "dept": course.dept,
            "number": course.number,
            "title": course.title,
            "description": course.description or "",
            "prerequisites": course.prerequisites or "",
            "instructors": course.instructors or "",
            "quarters": course.quarters or "",
        })
        docs.append(text)
        metas.append({"dept": course.dept, "number": course.number, "course_id": course.id})
        ids.append(f"course_{course.id}")

        if len(docs) >= BATCH_SIZE:
            collections["course_descriptions"].add(documents=docs, metadatas=metas, ids=ids)
            print(f"  Indexed {i + 1}/{len(courses)} courses...")
            docs, metas, ids = [], [], []

    # Flush remaining
    if docs:
        collections["course_descriptions"].add(documents=docs, metadatas=metas, ids=ids)
    print(f"  Indexed {len(courses)} courses total")

    # Index Reddit posts (if any)
    print("Indexing Reddit feedback...")
    posts = db.query(RedditPost).all()
    count = 0
    docs, metas, ids = [], [], []
    for post in posts:
        comments = db.query(RedditComment).filter_by(post_id=post.id).all()
        chunks = chunk_reddit_post(
            {"subreddit": post.subreddit, "title": post.title, "body": post.body or ""},
            [{"body": c.body, "score": c.score} for c in comments],
        )
        for j, chunk in enumerate(chunks):
            docs.append(chunk)
            metas.append({"post_id": post.id, "subreddit": post.subreddit})
            ids.append(f"reddit_{post.id}_{j}")
            count += 1

            if len(docs) >= BATCH_SIZE:
                collections["reddit_feedback"].add(documents=docs, metadatas=metas, ids=ids)
                docs, metas, ids = [], [], []

    if docs:
        collections["reddit_feedback"].add(documents=docs, metadatas=metas, ids=ids)
    print(f"  Indexed {count} Reddit chunks")

    # Index career listings (if any)
    print("Indexing career info...")
    listings = db.query(CareerListing).all()
    docs, metas, ids = [], [], []
    for listing in listings:
        text = f"{listing.title}\n{listing.description or ''}\nEmployer: {listing.employer or 'N/A'}"
        docs.append(text)
        metas.append({"type": listing.type or "", "listing_id": listing.id})
        ids.append(f"career_{listing.id}")

        if len(docs) >= BATCH_SIZE:
            collections["career_info"].add(documents=docs, metadatas=metas, ids=ids)
            docs, metas, ids = [], [], []

    if docs:
        collections["career_info"].add(documents=docs, metadatas=metas, ids=ids)
    print(f"  Indexed {len(listings)} career listings")

    db.close()
    print("Indexing complete!")
