"""
retrieval.py
------------
PolicyLens — Retrieval module.

Provides search functions that query ChromaDB with optional
metadata filtering (by country, document_type).
"""

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from config import (
    CHROMA_PERSIST_DIR, COLLECTION_NAME,
    EMBEDDING_MODEL, TOP_K, OLLAMA_BASE_URL
)


def get_vectorstore() -> Chroma:
    """
    Loads the existing ChromaDB collection.
    Call this once at app startup and reuse the returned object.
    """
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_BASE_URL)
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=embeddings
    )
    return vectorstore


def search_by_country(
    vectorstore: Chroma,
    query: str,
    country: str,
    top_k: int = TOP_K
) -> list:
    """
    Searches ChromaDB for chunks matching the query,
    filtered to a specific country.

    Args:
        vectorstore: The ChromaDB Chroma object
        query: The search query string
        country: Country to filter by (e.g., "South Africa", "Kenya")
        top_k: Number of results to return

    Returns:
        List of LangChain Document objects with metadata and similarity scores
    """
    results = vectorstore.similarity_search_with_relevance_scores(
        query=query,
        k=top_k,
        filter={"country": country}
    )
    return results


def search_all(
    vectorstore: Chroma,
    query: str,
    top_k: int = TOP_K
) -> list:
    """
    Searches all documents without country filtering.
    Useful for broad or exploratory queries.
    """
    results = vectorstore.similarity_search_with_relevance_scores(
        query=query,
        k=top_k
    )
    return results


RELEVANCE_THRESHOLD = 0.45  # Chunks below this score are too noisy to be useful


def format_context(results: list) -> str:
    """
    Formats search results into a readable context string
    for passing to the LLM.

    Each chunk is wrapped with its metadata (source, section, page)
    so the LLM can cite specific sections in its answer.

    Chunks with a relevance score below RELEVANCE_THRESHOLD are discarded
    to avoid passing noisy, off-topic passages to the synthesizer.
    """
    if not results:
        return "No relevant passages found."

    # Filter out low-confidence chunks before building context
    filtered = [(doc, score) for doc, score in results if score >= RELEVANCE_THRESHOLD]

    if not filtered:
        # All chunks fell below threshold — return a clear signal rather than noise
        return (
            f"No passages met the minimum relevance threshold ({RELEVANCE_THRESHOLD}). "
            "The documents may not contain specific provisions on this topic."
        )

    context_parts = []
    for i, (doc, score) in enumerate(filtered, 1):
        meta = doc.metadata
        context_parts.append(
            f"[Passage {i}] "
            f"(Source: {meta['document_name']}, "
            f"Section: {meta['section_heading']}, "
            f"Pages: {meta['start_page']}-{meta['end_page']}, "
            f"Relevance: {score:.3f})\n"
            f"{doc.page_content}"
        )

    return "\n\n---\n\n".join(context_parts)
