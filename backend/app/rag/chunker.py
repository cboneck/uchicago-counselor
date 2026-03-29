"""
Text chunking strategies for RAG embeddings.
"""


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks by word count."""
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)

    return chunks


def chunk_course(course: dict) -> str:
    """Create a searchable text chunk from a course record."""
    parts = [
        f"{course['dept']} {course['number']}: {course['title']}",
    ]
    if course.get("description"):
        parts.append(course["description"])
    if course.get("prerequisites"):
        parts.append(f"Prerequisites: {course['prerequisites']}")
    if course.get("instructors"):
        parts.append(f"Instructors: {course['instructors']}")
    if course.get("quarters"):
        parts.append(f"Offered: {course['quarters']}")

    return "\n".join(parts)


def chunk_reddit_post(post: dict, comments: list[dict]) -> list[str]:
    """Create searchable chunks from a Reddit post and its comments."""
    chunks = []

    # Post itself
    post_text = f"[Reddit r/{post['subreddit']}] {post['title']}\n{post['body']}"
    chunks.extend(chunk_text(post_text))

    # High-value comments (score > 1)
    for comment in sorted(comments, key=lambda c: c.get("score", 0), reverse=True):
        if comment.get("score", 0) > 1 and comment.get("body"):
            chunks.extend(chunk_text(comment["body"]))

    return chunks
