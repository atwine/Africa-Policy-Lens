"""
ingest.py
---------
PolicyLens Document Ingestion Pipeline.

Reads PDFs from docs/, cleans text, chunks with overlap,
embeds via Ollama nomic-embed-text, and stores in ChromaDB.

Usage:
    python ingest.py
"""

import os
import re
import sys

# Force UTF-8 output on Windows to handle any special characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import pdfplumber
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import (
    DOCUMENTS, CHROMA_PERSIST_DIR, COLLECTION_NAME,
    EMBEDDING_MODEL, CHUNK_SIZE_CHARS, CHUNK_OVERLAP_CHARS,
    OLLAMA_BASE_URL
)


def load_pdf(pdf_path: str) -> list[dict]:
    """
    Extracts text from a PDF file, page by page.

    Returns:
        List of dicts: [{"page_number": int, "text": str}, ...]
    """
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append({
                    "page_number": i + 1,
                    "text": text
                })
    print(f"  Extracted {len(pages)} pages from {os.path.basename(pdf_path)}")
    return pages


def clean_text(raw_text: str) -> str:
    """
    Cleans extracted PDF text:
    - Normalises line endings
    - Removes standalone page numbers
    - Collapses excessive whitespace
    - Fixes mid-sentence line breaks
    """
    text = raw_text.replace('\r\n', '\n').replace('\r', '\n')

    # Remove standalone page numbers at end of text
    text = re.sub(r'\n\d{1,3}\s*$', '', text.strip())

    # Collapse 3+ blank lines to 2
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Fix mid-sentence line breaks (line ends without punctuation,
    # next line starts with lowercase)
    text = re.sub(r'(?<![.!?:])\n(?=[a-z])', ' ', text)

    # Strip per-line whitespace
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(line for line in lines if line)

    return text.strip()


def detect_sections(pages: list[dict], source_name: str) -> list[dict]:
    """
    Groups consecutive pages into logical sections based on heading detection.
    Legal documents typically have well-structured chapter/section headings.

    Returns:
        List of section dicts with text and metadata.
    """
    sections = []
    current_section = {
        "source": source_name,
        "section_heading": "Preamble",
        "start_page": pages[0]["page_number"],
        "end_page": pages[0]["page_number"],
        "text": ""
    }

    for page in pages:
        cleaned = clean_text(page["text"])
        if not cleaned:
            continue

        first_line = cleaned.split('\n')[0].strip()

        # Detect new section: line is short (likely a heading),
        # starts with uppercase, and we already have content
        is_heading = (
            5 < len(first_line) < 100
            and not first_line[0].islower()
            and current_section["text"] != ""
            # Legal headings often start with "Chapter", "Part", "Section", or a number
        )

        if is_heading:
            if current_section["text"].strip():
                sections.append(current_section)
            current_section = {
                "source": source_name,
                "section_heading": first_line,
                "start_page": page["page_number"],
                "end_page": page["page_number"],
                "text": cleaned
            }
        else:
            current_section["text"] += '\n\n' + cleaned
            current_section["end_page"] = page["page_number"]

    # Don't forget the last section
    if current_section["text"].strip():
        sections.append(current_section)

    print(f"  Detected {len(sections)} sections")
    return sections


def chunk_and_tag(sections: list[dict], doc_meta: dict) -> list[Document]:
    """
    Splits sections into overlapping chunks and attaches metadata.

    Uses LangChain's RecursiveCharacterTextSplitter for intelligent
    splitting at sentence and paragraph boundaries.

    Returns:
        List of LangChain Document objects ready for ChromaDB.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE_CHARS,
        chunk_overlap=CHUNK_OVERLAP_CHARS,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    all_chunks = []
    chunk_index = 0

    for section in sections:
        text_chunks = splitter.split_text(section["text"])

        for chunk_text in text_chunks:
            doc = Document(
                page_content=chunk_text,
                metadata={
                    "country": doc_meta["country"],
                    "document_type": doc_meta["document_type"],
                    "document_name": doc_meta["document_name"],
                    "section_heading": section["section_heading"],
                    "start_page": section["start_page"],
                    "end_page": section["end_page"],
                    "chunk_index": chunk_index
                }
            )
            all_chunks.append(doc)
            chunk_index += 1

    print(f"  Generated {len(all_chunks)} chunks")
    return all_chunks


def main():
    """
    Main ingestion pipeline:
    1. Load each PDF
    2. Clean, section, and chunk the text
    3. Embed and store in ChromaDB
    """
    print("=" * 60)
    print("PolicyLens — Document Ingestion Pipeline")
    print("=" * 60)

    # Initialise the embedding model via Ollama (explicit base_url required)
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_BASE_URL)

    all_documents = []

    for filename, doc_meta in DOCUMENTS.items():
        pdf_path = os.path.join("docs", filename)

        if not os.path.exists(pdf_path):
            print(f"\n  WARNING: {pdf_path} not found — skipping.")
            continue

        print(f"\nProcessing: {filename}")
        print("-" * 40)

        pages = load_pdf(pdf_path)
        if not pages:
            continue

        sections = detect_sections(pages, filename)
        chunks = chunk_and_tag(sections, doc_meta)
        all_documents.extend(chunks)

    if not all_documents:
        print("\nERROR: No documents processed. Check that PDFs exist in docs/")
        return

    # Store in ChromaDB
    print(f"\n{'=' * 60}")
    print(f"Embedding and storing {len(all_documents)} chunks in ChromaDB...")
    print(f"This may take a few minutes on first run.")
    print(f"{'=' * 60}")

    vectorstore = Chroma.from_documents(
        documents=all_documents,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_PERSIST_DIR
    )

    print(f"\nDone! {len(all_documents)} chunks stored in '{CHROMA_PERSIST_DIR}'")
    print(f"Collection name: '{COLLECTION_NAME}'")

    # Print summary
    print(f"\n{'=' * 60}")
    print("INGESTION SUMMARY")
    print(f"{'=' * 60}")
    countries = set(doc.metadata["country"] for doc in all_documents)
    for country in sorted(countries):
        count = sum(1 for doc in all_documents if doc.metadata["country"] == country)
        print(f"  {country}: {count} chunks")
    print(f"  TOTAL: {len(all_documents)} chunks")


if __name__ == "__main__":
    main()
