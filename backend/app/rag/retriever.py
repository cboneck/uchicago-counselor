"""
RAG retrieval logic — query ChromaDB and return relevant context.
"""

import chromadb
from app.rag.embeddings import get_chroma_client, init_collections


class Retriever:
    def __init__(self):
        self.client = get_chroma_client()
        self.collections = init_collections(self.client)

    def search(
        self,
        query: str,
        collection_names: list[str] | None = None,
        n_results: int = 5,
    ) -> list[dict]:
        """
        Search across one or more collections and return ranked results.
        """
        if collection_names is None:
            collection_names = list(self.collections.keys())

        all_results = []

        for name in collection_names:
            collection = self.collections.get(name)
            if not collection:
                continue

            try:
                results = collection.query(
                    query_texts=[query],
                    n_results=n_results,
                )
            except Exception:
                continue

            if results and results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    all_results.append({
                        "source": name,
                        "text": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else None,
                    })

        # Sort by distance (lower = more relevant)
        all_results.sort(key=lambda r: r.get("distance") or float("inf"))
        return all_results[:n_results]

    def search_courses(self, query: str, n_results: int = 5) -> list[dict]:
        """Search specifically in course descriptions."""
        return self.search(query, ["course_descriptions"], n_results)

    def search_feedback(self, query: str, n_results: int = 5) -> list[dict]:
        """Search specifically in Reddit student feedback."""
        return self.search(query, ["reddit_feedback"], n_results)

    def search_careers(self, query: str, n_results: int = 5) -> list[dict]:
        """Search specifically in career information."""
        return self.search(query, ["career_info"], n_results)
