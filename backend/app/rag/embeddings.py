"""
ChromaDB embedding pipeline for RAG.
"""

import chromadb
from app.config import settings


def get_chroma_client() -> chromadb.PersistentClient:
    """Create a persistent ChromaDB client."""
    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(settings.chroma_path))


def get_or_create_collection(client: chromadb.PersistentClient, name: str):
    """Get or create a ChromaDB collection."""
    return client.get_or_create_collection(name=name)


def add_documents(
    collection,
    documents: list[str],
    metadatas: list[dict],
    ids: list[str],
):
    """Add documents to a ChromaDB collection."""
    # ChromaDB handles embedding automatically with its default model
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
    )


COLLECTIONS = {
    "course_descriptions": "Chunked course catalog entries",
    "reddit_feedback": "Student feedback from Reddit",
    "career_info": "Career and placement information",
    "major_requirements": "Major and minor track descriptions",
}


def init_collections(client: chromadb.PersistentClient) -> dict:
    """Initialize all ChromaDB collections."""
    return {
        name: get_or_create_collection(client, name)
        for name in COLLECTIONS
    }
