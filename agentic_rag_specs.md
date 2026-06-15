# African Data Protection Policy RAG Tool — MVP Specs Sheet

> **Project Codename:** PolicyLens (working title)
> **Version:** MVP v0.1
> **Author:** Mugume Twinamatsiko Atwine
> **Target Demo Date:** July 2, 2026 — ABI AI Community of Practice Meeting
> **Last Updated:** June 14, 2026

---

## 1. Project Overview

### 1.1 What This Is

A locally-run AI tool that answers complex questions about African data protection laws and policies. It uses an agentic retrieval-augmented generation (RAG) approach — meaning the system can break a question into sub-parts, search across multiple countries' laws, check if it has found enough information, and go back to search again if needed before producing a final answer.

### 1.2 Why Agentic RAG Instead of Standard RAG

Standard (vanilla) RAG does one search and generates one answer. This fails when:

- The answer requires information from multiple countries' laws (e.g., "Compare South Africa and Kenya on cross-border data sharing")
- The search terms in the question don't match the legal terminology in the documents (e.g., user says "data sharing" but the law says "transborder flow of personal information")
- The question requires reasoning across multiple document sections (e.g., "What gaps exist between national and continental frameworks?")

Agentic RAG solves these by introducing a planning step, iterative retrieval with sufficiency checks, and a synthesis step — turning a single lookup into a thorough research process.

### 1.3 Stakeholders

- **Sumir Panji (PhD)** — Program Manager, Computational Biology Division, University of Cape Town
- **Nicola Mulder** — University of Cape Town
- **Aida Ouangraoua** — AI Community of Practice (CoP) lead
- **Verena Ras** — Policy document curator, University of Cape Town
- **Mugume Twinamatsiko Atwine** — ML Engineer / Data Scientist, ACE, IDI Kampala (Builder)

### 1.4 Relationship to Existing Work

This builds upon an existing vanilla RAG pipeline (the Sanyu/CAPS chatbot) which uses pdfplumber for PDF extraction, sentence-transformers for embeddings, numpy dot-product for similarity search, and Gradio for the frontend. The new system upgrades the retrieval approach from single-pass to agentic multi-step, swaps the tech stack for local execution, and targets a completely different domain (legal policy analysis instead of health peer support).

---

## 2. MVP Scope

### 2.1 Documents (4 total)

| Document | Country/Scope | Type | Source URL |
|----------|--------------|------|------------|
| Protection of Personal Information Act (POPIA), 2013 | South Africa | Binding Law | https://popia.co.za/ or https://www.dlapiperdataprotection.com/guide.pdf?c=ZA |
| Data Protection Act No. 24 of 2019 | Kenya | Binding Law | https://www.interior.go.ke/sites/default/files/2024-09/27.%20Data%20Protection%20Act%202019.pdf |
| Data Protection and Privacy Act No. 9 of 2019 | Uganda | Binding Law | https://ict.go.ug/wp-content/uploads/2019/03/Data-Protection-and-Privacy-Act-2019.pdf |
| AU Convention on Cyber Security and Personal Data Protection (Malabo Convention), 2014 | Continental (African Union) | Binding Convention | https://ccdcoe.org/uploads/2018/11/AU-270614-CSConvention.pdf |

### 2.2 Metadata Tags Per Document Chunk

Each chunk stored in the vector database will carry the following metadata:

- `country`: One of `"South Africa"`, `"Kenya"`, `"Uganda"`, `"African Union"`
- `document_type`: One of `"binding_law"`, `"policy_strategy"` (all MVP documents are `"binding_law"`)
- `document_name`: Full name of the source document
- `section_heading`: The section or chapter heading the chunk belongs to
- `page_number`: The page(s) in the source PDF
- `chunk_index`: Sequential index within the document

### 2.3 Demo Questions (Preset Buttons in UI)

These four questions are hardcoded as clickable buttons in the Streamlit interface:

1. **Comparison:** "Where do the data protection laws of South Africa and Kenya align versus conflict with each other on data sharing for research?"

2. **Compliance:** "What conditions and safeguards are required for sharing health data between South Africa and Uganda?"

3. **Multi-country (Showstopper):** "What legal mechanisms currently support, and what gaps hinder, sharing public health data across South Africa, Kenya, and Uganda?"

4. **National vs Continental:** "What are the common themes between data governance at the national level versus the AU Malabo Convention, and where are there divergences?"

---

## 3. Architecture

### 3.1 High-Level Flow

```
User Question
     |
     v
[STAGE 1: PLANNER]
     |  - Identifies which countries/documents are relevant
     |  - Breaks question into sub-questions
     |  - Assigns each sub-question a target country/scope
     |
     v
[STAGE 2: RETRIEVER + EVALUATOR] (iterative loop)
     |  - For each sub-question:
     |      1. Search ChromaDB with metadata filter (country)
     |      2. Retrieve top-k relevant chunks
     |      3. LLM evaluates: "Is this enough to answer the sub-question?"
     |         - If YES: move to next sub-question
     |         - If NO: rewrite the query and search again (max 2 retries)
     |
     v
[STAGE 3: SYNTHESIZER]
     |  - Receives all retrieved context from all sub-questions
     |  - Generates a comprehensive, formal answer
     |  - Cites specific sections of the laws
     |
     v
Final Answer (displayed in Streamlit)
```

### 3.2 Stage 1 — The Planner

**Input:** Raw user question (string)

**What it does:** Sends the question to the LLM with a planning prompt. The LLM returns a structured plan (JSON) containing a list of sub-questions, each with a target country/scope to filter by, and the reasoning for the breakdown.

**Output:** JSON object, example:

```json
{
  "reasoning": "This question requires comparing two countries' positions on cross-border data sharing for research purposes.",
  "sub_questions": [
    {
      "question": "What does South Africa's POPIA say about conditions for cross-border transfer of personal data, specifically for research purposes?",
      "target_country": "South Africa",
      "priority": 1
    },
    {
      "question": "What does Kenya's Data Protection Act say about cross-border transfer of personal data, specifically for research purposes?",
      "target_country": "Kenya",
      "priority": 2
    },
    {
      "question": "What does the AU Malabo Convention say about cross-border data transfer requirements that member states should follow?",
      "target_country": "African Union",
      "priority": 3
    }
  ]
}
```

**Planner System Prompt Guidelines:**

- Instruct the model to always consider the AU Malabo Convention as a supplementary source when comparing national laws
- Instruct the model to output valid JSON only
- Limit sub-questions to a maximum of 5 per user question
- Each sub-question should be self-contained and searchable

### 3.3 Stage 2 — The Retriever + Evaluator

**Input:** List of sub-questions with target countries from Stage 1

**What it does (for each sub-question):**

1. Queries ChromaDB with the sub-question text as search query, metadata filter `country == target_country`, returns top 5 chunks
2. Passes retrieved chunks to LLM with evaluation prompt asking: "Given these retrieved passages, do you have sufficient context to answer this sub-question? Respond with SUFFICIENT or INSUFFICIENT and explain what is missing."
3. If INSUFFICIENT and retries remain (max 2 per sub-question): LLM generates a rewritten search query, system searches again, chunks are added (deduplicated), sufficiency check repeats
4. If SUFFICIENT or max retries reached: move to next sub-question

**Output:** A dictionary mapping each sub-question to its retrieved context chunks

**Evaluator System Prompt Guidelines:**

- Be strict about sufficiency — if the question asks about "conditions for cross-border transfer" and the chunks only mention "data processing principles," that is INSUFFICIENT
- When generating a rewritten query, suggest alternative legal terminology (e.g., "transborder flow" instead of "cross-border transfer")
- Keep rewritten queries concise (under 20 words)

### 3.4 Stage 3 — The Synthesizer

**Input:** Original user question + all retrieved context chunks from Stage 2

**What it does:** Sends everything to the LLM with a synthesis prompt that instructs it to write a comprehensive, formal answer.

**Output:** A well-structured text response

**Synthesizer System Prompt Guidelines:**

- Persona: Knowledgeable legal research assistant — formal, precise, authoritative
- Always cite specific sections of the laws (e.g., "Section 72(1)(a) of POPIA")
- For comparison questions: use a structured format showing alignments and conflicts
- For compliance questions: list specific requirements from each jurisdiction
- For gap analysis questions: clearly identify what is covered and what is missing
- Always include disclaimer: "This analysis is generated by an AI system for research purposes and does not constitute legal advice."
- If context was insufficient for any sub-question, explicitly state what could not be determined

---

## 4. Tech Stack

### 4.1 Summary

| Component | Technology | Purpose |
|-----------|-----------|---------|
| LLM (reasoning) | Llama 3.1 8B via Ollama | Planning, evaluation, synthesis |
| Embeddings | nomic-embed-text via Ollama | Converting text chunks to vectors |
| Vector Store | ChromaDB (local, persistent) | Storing and searching chunks with metadata filtering |
| Orchestration | LangGraph | Managing the three-stage flow with conditional iteration |
| Document Parsing | pdfplumber | Extracting text from PDF policy documents |
| Frontend | Streamlit | User interface with preset buttons and process visibility |
| Runtime | Python 3.10+ | All components |

### 4.2 Ollama Models

```bash
# Models required (run these commands to install)
ollama pull llama3.1:8b          # Main reasoning model (~4.7GB)
ollama pull nomic-embed-text     # Embedding model (~274MB)
```

### 4.3 Python Dependencies

```txt
# requirements.txt

# Core framework
langgraph>=0.2.0
langchain>=0.3.0
langchain-ollama>=0.3.0
langchain-chroma>=0.2.0
langchain-core>=0.3.0

# Document processing
pdfplumber>=0.11.0

# Vector store
chromadb>=0.5.0

# Frontend
streamlit>=1.38.0

# Utilities
numpy>=1.24.0
```

---

## 5. Project Setup — Step by Step

### 5.1 Create the Project Folder Structure

The project root is: `C:\Users\ic\OneDrive\Desktop\PolicyBot`

Run these commands from within that directory:

```bash
# Navigate to the project root
cd C:\Users\ic\OneDrive\Desktop\PolicyBot

# Create subdirectories
mkdir docs
mkdir chroma_db
mkdir prompts

# Create empty Python files (Windows)
type nul > config.py
type nul > ingest.py
type nul > retrieval.py
type nul > nodes.py
type nul > graph.py
type nul > app.py
type nul > requirements.txt
```

### 5.2 Final Folder Structure with File Descriptions

```
C:\Users\ic\OneDrive\Desktop\PolicyBot\
│
├── requirements.txt          # Python dependencies (see Section 4.3)
├── config.py                 # All configuration constants in one place
├── ingest.py                 # Document ingestion pipeline — run once to load PDFs into ChromaDB
├── retrieval.py              # ChromaDB search utilities with metadata filtering
├── nodes.py                  # LangGraph node functions (plan, retrieve, evaluate, rewrite, synthesize)
├── graph.py                  # LangGraph flow definition — wires all nodes together
├── app.py                    # Streamlit frontend — the user-facing demo app
│
├── prompts\                  # All LLM system prompts as separate text files for easy editing
│   ├── planner.txt           # System prompt for Stage 1 (Planner)
│   ├── evaluator.txt         # System prompt for Stage 2 (Evaluator / sufficiency check)
│   ├── rewriter.txt          # System prompt for Stage 2 (Query rewriter)
│   └── synthesizer.txt       # System prompt for Stage 3 (Final answer generation)
│
├── docs\                     # Source PDF documents — download these manually
│   ├── south_africa_popia.pdf
│   ├── kenya_dpa_2019.pdf
│   ├── uganda_dppa_2019.pdf
│   └── au_malabo_convention.pdf
│
└── chroma_db\                # ChromaDB persistent storage (auto-created by ingest.py)
```

### 5.3 Install Dependencies

```bash
# Create and activate a virtual environment
cd C:\Users\ic\OneDrive\Desktop\PolicyBot
python -m venv venv

# On Windows:
venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

### 5.4 Download the Source PDFs

Download these files manually and place them in the `docs/` folder:

```
docs/south_africa_popia.pdf   ← from https://www.dlapiperdataprotection.com/guide.pdf?c=ZA
docs/kenya_dpa_2019.pdf       ← from https://www.interior.go.ke/sites/default/files/2024-09/27.%20Data%20Protection%20Act%202019.pdf
docs/uganda_dppa_2019.pdf     ← from https://ict.go.ug/wp-content/uploads/2019/03/Data-Protection-and-Privacy-Act-2019.pdf
docs/au_malabo_convention.pdf ← from https://ccdcoe.org/uploads/2018/11/AU-270614-CSConvention.pdf
```

### 5.5 Verify Ollama Is Running

```bash
# Check Ollama is running and models are available
ollama list

# Expected output should include:
# llama3.1:8b
# nomic-embed-text:latest

# If Ollama is not running:
ollama serve
```

---

## 6. File-by-File Implementation

### 6.1 config.py — Configuration Constants

This file is the single source of truth for all settings. Every other file imports from here.

```python
"""
config.py
---------
Central configuration for PolicyLens.
All constants in one place — change settings here, not in individual files.
"""

# ---------------------------------------------------------------------------
# Ollama settings
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL = "llama3.1:8b"
EMBEDDING_MODEL = "nomic-embed-text"
LLM_TEMPERATURE = 0.1  # Low temperature for precise, deterministic legal analysis

# ---------------------------------------------------------------------------
# ChromaDB settings
# ---------------------------------------------------------------------------
CHROMA_PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "policy_documents"

# ---------------------------------------------------------------------------
# Chunking settings (used by ingest.py)
# ---------------------------------------------------------------------------
CHUNK_SIZE_CHARS = 1500       # ~375 tokens — smaller than typical because legal text is dense
CHUNK_OVERLAP_CHARS = 200     # ~50 tokens overlap to avoid cutting mid-sentence

# ---------------------------------------------------------------------------
# Retrieval settings (used by nodes.py)
# ---------------------------------------------------------------------------
TOP_K = 5                     # Number of chunks returned per search query
MAX_RETRIES = 2               # Max query rewrites per sub-question
MAX_SUB_QUESTIONS = 5         # Max sub-questions the planner can generate

# ---------------------------------------------------------------------------
# Document registry
# Maps PDF filenames (in docs/) to their metadata.
# When adding new documents, add an entry here and place the PDF in docs/.
# ---------------------------------------------------------------------------
DOCUMENTS = {
    "south_africa_popia.pdf": {
        "country": "South Africa",
        "document_type": "binding_law",
        "document_name": "Protection of Personal Information Act (POPIA), 2013"
    },
    "kenya_dpa_2019.pdf": {
        "country": "Kenya",
        "document_type": "binding_law",
        "document_name": "Data Protection Act No. 24 of 2019"
    },
    "uganda_dppa_2019.pdf": {
        "country": "Uganda",
        "document_type": "binding_law",
        "document_name": "Data Protection and Privacy Act No. 9 of 2019"
    },
    "au_malabo_convention.pdf": {
        "country": "African Union",
        "document_type": "binding_law",
        "document_name": "AU Convention on Cyber Security and Personal Data Protection (Malabo Convention), 2014"
    }
}

# ---------------------------------------------------------------------------
# Demo preset questions (displayed as buttons in Streamlit UI)
# ---------------------------------------------------------------------------
DEMO_QUESTIONS = [
    "Where do the data protection laws of South Africa and Kenya align versus conflict with each other on data sharing for research?",
    "What conditions and safeguards are required for sharing health data between South Africa and Uganda?",
    "What legal mechanisms currently support, and what gaps hinder, sharing public health data across South Africa, Kenya, and Uganda?",
    "What are the common themes between data governance at the national level versus the AU Malabo Convention, and where are there divergences?"
]
```

### 6.2 ingest.py — Document Ingestion Pipeline

Run this once to process all PDFs and load them into ChromaDB. Re-run when new documents are added.

```python
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
import pdfplumber
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import (
    DOCUMENTS, CHROMA_PERSIST_DIR, COLLECTION_NAME,
    EMBEDDING_MODEL, CHUNK_SIZE_CHARS, CHUNK_OVERLAP_CHARS
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

    # Initialise the embedding model via Ollama
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

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
```

### 6.3 retrieval.py — ChromaDB Search Utilities

```python
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
    EMBEDDING_MODEL, TOP_K
)


def get_vectorstore() -> Chroma:
    """
    Loads the existing ChromaDB collection.
    Call this once at app startup and reuse the returned object.
    """
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
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


def format_context(results: list) -> str:
    """
    Formats search results into a readable context string
    for passing to the LLM.

    Each chunk is wrapped with its metadata (source, section, page)
    so the LLM can cite specific sections in its answer.
    """
    if not results:
        return "No relevant passages found."

    context_parts = []
    for i, (doc, score) in enumerate(results, 1):
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
```

### 6.4 nodes.py — LangGraph Node Functions

Each function here is a "node" in the LangGraph flow. It receives the current state, does its work, and returns updated state fields.

```python
"""
nodes.py
--------
PolicyLens — LangGraph node functions.

Each function corresponds to a node in the agentic RAG graph.
Functions receive the full state dict and return a dict of
fields to update.
"""

import json
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from retrieval import get_vectorstore, search_by_country, format_context
from config import LLM_MODEL, LLM_TEMPERATURE, MAX_RETRIES, TOP_K


# ---------------------------------------------------------------------------
# Initialise shared resources (loaded once, reused across calls)
# ---------------------------------------------------------------------------
llm = ChatOllama(model=LLM_MODEL, temperature=LLM_TEMPERATURE)
vectorstore = get_vectorstore()


# ---------------------------------------------------------------------------
# Helper: Load prompt from file
# ---------------------------------------------------------------------------
def load_prompt(filename: str) -> str:
    """Loads a system prompt from the prompts/ directory."""
    with open(f"prompts/{filename}", "r") as f:
        return f.read().strip()


# ---------------------------------------------------------------------------
# STAGE 1: Planner
# ---------------------------------------------------------------------------
def plan_node(state: dict) -> dict:
    """
    Takes the user's question and produces a research plan:
    a list of sub-questions, each targeting a specific country.

    Updates: plan, sub_questions, current_sub_question_index, process_log
    """
    system_prompt = load_prompt("planner.txt")
    user_question = state["user_question"]

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"User question: {user_question}")
    ])

    # Parse the JSON from the LLM response
    # The LLM may wrap JSON in markdown code blocks — strip those
    raw = response.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        plan = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: if JSON parsing fails, create a single sub-question
        # searching all countries
        plan = {
            "reasoning": "Could not parse plan. Falling back to broad search.",
            "sub_questions": [
                {
                    "question": user_question,
                    "target_country": "all",
                    "priority": 1
                }
            ]
        }

    sub_questions = plan.get("sub_questions", [])

    # Build process log entries
    log = [f"📋 **Planning:** Identified {len(sub_questions)} sub-questions"]
    for i, sq in enumerate(sub_questions, 1):
        log.append(f"  {i}. [{sq['target_country']}] {sq['question']}")

    return {
        "plan": plan,
        "sub_questions": sub_questions,
        "current_sub_question_index": 0,
        "retrieved_chunks": {},
        "retry_count": 0,
        "process_log": state.get("process_log", []) + log
    }


# ---------------------------------------------------------------------------
# STAGE 2a: Retriever
# ---------------------------------------------------------------------------
def retrieve_node(state: dict) -> dict:
    """
    Searches ChromaDB for the current sub-question,
    filtered by the target country.

    Updates: retrieved_chunks (adds to existing), current_query, process_log
    """
    idx = state["current_sub_question_index"]
    sq = state["sub_questions"][idx]
    query = state.get("current_query", sq["question"])
    target_country = sq["target_country"]

    log_entry = f"🔍 **Searching** {target_country}: \"{query[:80]}...\""

    # Perform the search
    if target_country == "all":
        from retrieval import search_all
        results = search_all(vectorstore, query, top_k=TOP_K)
    else:
        results = search_by_country(vectorstore, query, target_country, top_k=TOP_K)

    # Format context from results
    context = format_context(results)

    # Store results keyed by sub-question index
    retrieved = state.get("retrieved_chunks", {})
    existing = retrieved.get(str(idx), "")
    if existing:
        # Append new results (for retry iterations)
        retrieved[str(idx)] = existing + "\n\n---\n\n" + context
    else:
        retrieved[str(idx)] = context

    log_entry += f"\n  Found {len(results)} relevant passages"

    return {
        "retrieved_chunks": retrieved,
        "current_query": query,
        "process_log": state.get("process_log", []) + [log_entry]
    }


# ---------------------------------------------------------------------------
# STAGE 2b: Evaluator (Sufficient Context Check)
# ---------------------------------------------------------------------------
def evaluate_node(state: dict) -> dict:
    """
    Checks if the retrieved context is sufficient to answer
    the current sub-question.

    Updates: sufficiency_status, process_log
    """
    idx = state["current_sub_question_index"]
    sq = state["sub_questions"][idx]
    context = state["retrieved_chunks"].get(str(idx), "")

    system_prompt = load_prompt("evaluator.txt")

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=(
            f"Sub-question: {sq['question']}\n\n"
            f"Retrieved context:\n{context}"
        ))
    ])

    answer = response.content.strip().upper()
    status = "SUFFICIENT" if "SUFFICIENT" in answer and "INSUFFICIENT" not in answer else "INSUFFICIENT"

    if status == "SUFFICIENT":
        log_entry = f"✅ **Context check:** SUFFICIENT for [{sq['target_country']}]"
    else:
        log_entry = f"⚠️ **Context check:** INSUFFICIENT for [{sq['target_country']}] — will retry"

    return {
        "sufficiency_status": status,
        "process_log": state.get("process_log", []) + [log_entry]
    }


# ---------------------------------------------------------------------------
# STAGE 2c: Query Rewriter
# ---------------------------------------------------------------------------
def rewrite_node(state: dict) -> dict:
    """
    When context is insufficient, rewrites the search query
    using alternative legal terminology.

    Updates: current_query, retry_count, process_log
    """
    idx = state["current_sub_question_index"]
    sq = state["sub_questions"][idx]
    context = state["retrieved_chunks"].get(str(idx), "")

    system_prompt = load_prompt("rewriter.txt")

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=(
            f"Original sub-question: {sq['question']}\n\n"
            f"Previous search returned insufficient context. "
            f"Generate a rewritten search query using different legal terminology."
        ))
    ])

    new_query = response.content.strip().strip('"').strip("'")
    retry_count = state.get("retry_count", 0) + 1

    log_entry = f"🔄 **Rewriting query** (attempt {retry_count}): \"{new_query[:80]}...\""

    return {
        "current_query": new_query,
        "retry_count": retry_count,
        "process_log": state.get("process_log", []) + [log_entry]
    }


# ---------------------------------------------------------------------------
# STAGE 2d: Advance to Next Sub-question
# ---------------------------------------------------------------------------
def advance_node(state: dict) -> dict:
    """
    Moves to the next sub-question and resets retry state.

    Updates: current_sub_question_index, retry_count, current_query
    """
    next_idx = state["current_sub_question_index"] + 1

    # Reset query to the next sub-question's text (if there is one)
    if next_idx < len(state["sub_questions"]):
        next_query = state["sub_questions"][next_idx]["question"]
    else:
        next_query = ""

    return {
        "current_sub_question_index": next_idx,
        "retry_count": 0,
        "current_query": next_query
    }


# ---------------------------------------------------------------------------
# STAGE 3: Synthesizer
# ---------------------------------------------------------------------------
def synthesize_node(state: dict) -> dict:
    """
    Combines all retrieved context and generates the final,
    comprehensive answer with legal citations.

    Updates: final_answer, process_log
    """
    system_prompt = load_prompt("synthesizer.txt")
    user_question = state["user_question"]

    # Build the full context from all sub-questions
    full_context_parts = []
    for i, sq in enumerate(state["sub_questions"]):
        context = state["retrieved_chunks"].get(str(i), "No context retrieved.")
        full_context_parts.append(
            f"--- Sub-question {i+1}: {sq['question']} ---\n"
            f"Target: {sq['target_country']}\n\n"
            f"{context}"
        )

    full_context = "\n\n" + "=" * 40 + "\n\n".join(full_context_parts)

    log_entry = "📝 **Synthesizing** final answer..."

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=(
            f"Original user question: {user_question}\n\n"
            f"Research findings:\n{full_context}\n\n"
            f"Please provide a comprehensive, formal answer with specific legal citations."
        ))
    ])

    final_answer = response.content.strip()

    # Append disclaimer
    disclaimer = (
        "\n\n---\n*Disclaimer: This analysis is generated by an AI system "
        "for research purposes and does not constitute legal advice.*"
    )
    final_answer += disclaimer

    return {
        "final_answer": final_answer,
        "process_log": state.get("process_log", []) + [log_entry, "✅ **Done!**"]
    }
```

### 6.5 graph.py — LangGraph Flow Definition

This wires all the nodes together into the agentic flow with conditional edges.

```python
"""
graph.py
--------
PolicyLens — LangGraph flow definition.

Defines the three-stage agentic RAG pipeline:
  Plan → Retrieve → Evaluate → (Rewrite?) → Advance → Synthesize

The graph uses conditional edges to implement:
  1. The retry loop (evaluate → rewrite → retrieve if insufficient)
  2. The sub-question loop (advance → retrieve if more sub-questions remain)
"""

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END, START
from nodes import (
    plan_node, retrieve_node, evaluate_node,
    rewrite_node, advance_node, synthesize_node
)
from config import MAX_RETRIES


# ---------------------------------------------------------------------------
# State schema
# ---------------------------------------------------------------------------
class PolicyRAGState(TypedDict):
    # Input
    user_question: str

    # Stage 1 output
    plan: dict
    sub_questions: list
    current_sub_question_index: int

    # Stage 2 working state
    current_query: str
    current_target_country: str
    retrieved_chunks: dict       # Map: sub-question index (str) -> context string
    retry_count: int
    sufficiency_status: str      # "SUFFICIENT" or "INSUFFICIENT"

    # Stage 3 output
    final_answer: str

    # Process log (for Streamlit UI display)
    process_log: list


# ---------------------------------------------------------------------------
# Routing functions (conditional edges)
# ---------------------------------------------------------------------------
def should_retry_or_advance(state: dict) -> str:
    """
    After evaluation, decides whether to:
    - Retry (rewrite query and search again) if context is insufficient
    - Advance to the next sub-question if sufficient or max retries reached
    """
    if (
        state["sufficiency_status"] == "INSUFFICIENT"
        and state["retry_count"] < MAX_RETRIES
    ):
        return "rewrite"
    else:
        return "advance"


def has_more_subquestions(state: dict) -> str:
    """
    After advancing, decides whether to:
    - Continue retrieving (more sub-questions remain)
    - Proceed to synthesis (all sub-questions handled)
    """
    if state["current_sub_question_index"] < len(state["sub_questions"]):
        return "retrieve"
    else:
        return "synthesize"


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------
def build_graph():
    """
    Constructs and compiles the LangGraph StateGraph.

    Graph structure:
        START → plan → retrieve → evaluate
                          ↑            |
                          |            ├─ (INSUFFICIENT + retries left) → rewrite → retrieve
                          |            |
                          |            └─ (SUFFICIENT or max retries) → advance
                          |                                                |
                          +── (more sub-questions) ────────────────────────+
                                                                          |
                                                    (all done) → synthesize → END
    """
    graph = StateGraph(PolicyRAGState)

    # Add all nodes
    graph.add_node("plan", plan_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("evaluate", evaluate_node)
    graph.add_node("rewrite", rewrite_node)
    graph.add_node("advance", advance_node)
    graph.add_node("synthesize", synthesize_node)

    # Wire the edges
    graph.add_edge(START, "plan")          # Entry point
    graph.add_edge("plan", "retrieve")     # Plan → first retrieval
    graph.add_edge("retrieve", "evaluate") # Retrieve → check sufficiency

    # Conditional: after evaluation, retry or advance?
    graph.add_conditional_edges(
        "evaluate",
        should_retry_or_advance,
        {
            "rewrite": "rewrite",
            "advance": "advance"
        }
    )

    graph.add_edge("rewrite", "retrieve")  # Rewrite → search again

    # Conditional: after advancing, more sub-questions or synthesize?
    graph.add_conditional_edges(
        "advance",
        has_more_subquestions,
        {
            "retrieve": "retrieve",
            "synthesize": "synthesize"
        }
    )

    graph.add_edge("synthesize", END)      # Synthesize → done

    # Compile the graph
    compiled = graph.compile()
    return compiled


# ---------------------------------------------------------------------------
# Convenience function for running a query
# ---------------------------------------------------------------------------
def run_query(question: str) -> dict:
    """
    Runs a question through the full agentic RAG pipeline.

    Args:
        question: The user's natural language question

    Returns:
        The final state dict containing:
        - final_answer: The synthesized response
        - process_log: List of log messages for UI display
        - All intermediate state
    """
    graph = build_graph()
    initial_state = {
        "user_question": question,
        "plan": {},
        "sub_questions": [],
        "current_sub_question_index": 0,
        "current_query": "",
        "current_target_country": "",
        "retrieved_chunks": {},
        "retry_count": 0,
        "sufficiency_status": "",
        "final_answer": "",
        "process_log": []
    }

    final_state = graph.invoke(initial_state)
    return final_state
```

### 6.6 app.py — Streamlit Frontend

```python
"""
app.py
------
PolicyLens — Streamlit Frontend.

Provides:
- 4 preset demo question buttons
- Free-text input
- Real-time process log display
- Formatted final answer with citations

Usage:
    streamlit run app.py
"""

import streamlit as st
from graph import run_query
from config import DEMO_QUESTIONS


# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="PolicyLens",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ PolicyLens")
st.markdown(
    "**African Data Protection Policy Assistant** — "
    "Agentic RAG for cross-country legal analysis"
)
st.markdown("---")


# ---------------------------------------------------------------------------
# Preset question buttons
# ---------------------------------------------------------------------------
st.subheader("Demo Questions")
st.markdown("Click a question to run it through the agentic pipeline:")

# Use columns to lay out buttons side by side
col1, col2 = st.columns(2)

selected_question = None

with col1:
    if st.button("🔀 Compare SA & Kenya", use_container_width=True):
        selected_question = DEMO_QUESTIONS[0]
    if st.button("🌍 Multi-country gaps", use_container_width=True):
        selected_question = DEMO_QUESTIONS[2]

with col2:
    if st.button("✅ Compliance: SA & Uganda", use_container_width=True):
        selected_question = DEMO_QUESTIONS[1]
    if st.button("🏛️ National vs AU", use_container_width=True):
        selected_question = DEMO_QUESTIONS[3]

st.markdown("---")

# ---------------------------------------------------------------------------
# Free-text input
# ---------------------------------------------------------------------------
st.subheader("Or ask your own question")
custom_question = st.text_area(
    "Type your question here:",
    height=80,
    placeholder="e.g., What consent requirements apply to health data research in Uganda?"
)

if st.button("🚀 Ask", use_container_width=True):
    if custom_question.strip():
        selected_question = custom_question.strip()
    else:
        st.warning("Please type a question first.")

# ---------------------------------------------------------------------------
# Run the pipeline and display results
# ---------------------------------------------------------------------------
if selected_question:
    st.markdown("---")
    st.markdown(f"**Question:** {selected_question}")

    # Process log container
    with st.status("🔄 Running agentic RAG pipeline...", expanded=True) as status:
        result = run_query(selected_question)

        # Display the process log
        for log_entry in result.get("process_log", []):
            st.markdown(log_entry)

        status.update(label="✅ Pipeline complete!", state="complete")

    # Display the final answer
    st.markdown("---")
    st.subheader("📄 Analysis")
    st.markdown(result.get("final_answer", "No answer generated."))
```

### 6.7 prompts/ — System Prompt Files

These are plain text files. Keeping prompts separate from code makes them easy to edit and tune without touching Python.

**prompts/planner.txt:**

```
You are a legal research planning assistant. Your job is to break down a user's question about African data protection laws into specific sub-questions that can be searched independently.

Available countries in the knowledge base: South Africa, Kenya, Uganda, African Union (Malabo Convention).

Rules:
1. Output ONLY valid JSON, no other text.
2. Each sub-question should target ONE specific country or "African Union".
3. Maximum 5 sub-questions.
4. When the user asks about comparisons between countries, create one sub-question per country.
5. When relevant, always include a sub-question for the AU Malabo Convention as it provides the continental framework.
6. Each sub-question should be self-contained and specific enough to search against legal document text.
7. Use legal terminology that would appear in data protection legislation (e.g., "cross-border transfer", "transborder flow", "data subject rights", "processing conditions").

Output format:
{
  "reasoning": "Brief explanation of why you broke it down this way",
  "sub_questions": [
    {
      "question": "The specific sub-question to search for",
      "target_country": "Country name exactly as listed above",
      "priority": 1
    }
  ]
}
```

**prompts/evaluator.txt:**

```
You are a legal research quality checker. Your job is to determine whether the retrieved passages contain SUFFICIENT information to answer the given sub-question.

Rules:
1. Start your response with exactly "SUFFICIENT" or "INSUFFICIENT" (all caps).
2. Then explain your reasoning in 1-2 sentences.
3. Be STRICT: if the sub-question asks about cross-border data transfer but the passages only discuss general data processing principles, that is INSUFFICIENT.
4. If the passages mention the relevant topic but lack specific legal provisions, sections, or conditions, that is INSUFFICIENT.
5. If the passages contain at least one directly relevant legal provision with enough detail to form part of an answer, that is SUFFICIENT.

Examples:
- Sub-question asks about "consent requirements for health data" and passages discuss consent in general terms → INSUFFICIENT (need health-data-specific provisions)
- Sub-question asks about "cross-border transfer conditions" and passages contain Section 72 detailing adequacy requirements → SUFFICIENT
```

**prompts/rewriter.txt:**

```
You are a legal search query specialist. The previous search query did not return sufficient results from African data protection law documents.

Your job: generate ONE rewritten search query using alternative legal terminology that might appear in the actual legislation.

Rules:
1. Output ONLY the rewritten query — no explanation, no quotes, no extra text.
2. Keep it under 20 words.
3. Use different legal terms than the original (e.g., if "cross-border transfer" failed, try "transborder flow of personal information" or "transfer to third party in foreign jurisdiction").
4. Consider that African data protection laws draw heavily from GDPR terminology.

Common alternative phrasings in African data protection law:
- "data sharing" → "transfer of personal information to third party"
- "cross-border transfer" → "transborder flow" or "transfer to foreign jurisdiction"
- "consent" → "prior authorisation" or "data subject agreement"
- "health data" → "special personal information" or "sensitive personal data"
- "safeguards" → "adequate level of protection" or "appropriate security measures"
- "research" → "processing for historical, statistical or research purposes"
```

**prompts/synthesizer.txt:**

```
You are a knowledgeable legal research assistant specialising in African data protection law. Your task is to synthesize research findings into a comprehensive, formal answer.

Persona: Formal, precise, authoritative. You cite specific sections of legislation.

Rules:
1. Always cite specific legal provisions (e.g., "Section 72(1)(a) of South Africa's POPIA", "Section 48 of Kenya's Data Protection Act 2019").
2. Structure your answer clearly:
   - For COMPARISON questions: Present each country's position, then highlight alignments and conflicts.
   - For COMPLIANCE questions: List specific requirements from each jurisdiction in a structured format.
   - For GAP ANALYSIS questions: Identify what is covered by each framework and what is missing.
3. If the research findings were insufficient for any aspect, explicitly state: "The available documents did not contain sufficient detail on [topic]. Further research is recommended."
4. Use formal, precise language appropriate for a policy audience.
5. Do NOT fabricate legal provisions. Only cite sections that appear in the retrieved context.
6. Keep the answer focused and structured — use headers to organise sections when comparing multiple countries.
7. End with a brief summary of key takeaways.
```

---

## 7. Running the System

### 7.1 First-Time Setup (run once)

```bash
# 1. Make sure Ollama is running
ollama serve

# 2. Navigate to project directory
cd C:\Users\ic\OneDrive\Desktop\PolicyBot

# 3. Activate virtual environment
venv\Scripts\activate

# 4. Run the ingestion pipeline to load documents into ChromaDB
python ingest.py

# Expected output:
# PolicyLens — Document Ingestion Pipeline
# Processing: south_africa_popia.pdf
#   Extracted 45 pages
#   Detected 12 sections
#   Generated 87 chunks
# ... (similar for each document)
# Embedding and storing 350 chunks in ChromaDB...
# Done!
```

### 7.2 Running the App

```bash
# Make sure Ollama is running, then:
streamlit run app.py

# This opens a browser tab at http://localhost:8501
# Click any preset question button to run the pipeline
```

---

## 8. Hardware Requirements

| Resource | Minimum | Available |
|----------|---------|-----------|
| GPU | NVIDIA GPU with 6GB VRAM | NVIDIA RTX 3050 (6GB) |
| System RAM | 16GB | 24GB DDR5 |
| Storage | 10GB free | NVMe SSD |
| CUDA | 11.8+ | 12.7 |
| OS | Windows 10/11 or Linux | Windows |

---

## 9. Development and Testing Plan

### Phase 1 — Document Ingestion (Day 1-2)
- Download all 4 PDFs
- Run `python ingest.py`
- Verify chunks in ChromaDB (spot-check metadata, chunk quality)
- Test basic retrieval with simple queries via `retrieval.py` to confirm embedding quality

### Phase 2 — LangGraph Pipeline (Day 3-5)
- Implement `nodes.py` functions
- Wire up `graph.py`
- Test Stage 1 (Planner) in isolation — does it produce sensible sub-questions?
- Test Stage 2 (Retriever + Evaluator) — does sufficiency check work? Does rewriting help?
- Test Stage 3 (Synthesizer) — does it produce formal, cited answers?
- Connect all stages and test end-to-end with the 4 preset questions

### Phase 3 — Streamlit UI (Day 6-7)
- Build `app.py` layout with preset buttons and text input
- Connect to LangGraph flow
- Implement real-time process log display using `st.status`
- Style and polish for demo readiness

### Phase 4 — Testing and Prompt Tuning (Day 8-10)
- Run all 4 preset questions multiple times
- Tune prompt files in `prompts/` based on output quality
- Test edge cases: vague questions, questions about countries not in the database
- Prepare for demo

---

## 10. Future Extensions (Post-MVP)

Not in scope for July 2 demo, but noted for planning:

- **More countries:** Add documents for additional African nations as they become available from Verena
- **Document categories:** Support for policy/strategy documents (e.g., STISA 2034) with Sumir's categorization
- **Parallel retrieval:** With better hardware (e.g., A100), split into full Google-style pipeline with separate agents
- **Hugging Face Spaces deployment:** Package for cloud deployment so CoP members can test remotely
- **DTA/MTA generation:** Assist in generating Data Transfer Agreements based on applicable laws
- **Side-by-side comparison view:** UI showing two countries' provisions next to each other
- **Citation linking:** Link citations to specific pages in source PDFs
- **Document updates:** Process for ingesting updated versions of laws
- **AI-specific queries:** Support Aida's questions about consent for AI-based health applications

---

## 11. Key References

### Architecture Inspiration
- Google Research: "Unlocking Dependable Responses with Gemini Enterprise Agent Platforms: Agentic RAG"
  https://research.google/blog/unlocking-dependable-responses-with-gemini-enterprise-agent-platforms-agentic-rag/

### Academic References
- MA-RAG: Multi-Agent RAG via Collaborative Chain-of-Thought Reasoning (2024)
- HM-RAG: Hierarchical Multi-Agent RAG — 12.95% accuracy improvement via multi-source retrieval
- MAO-ARAG: Adaptive Agentic RAG with iterative context evaluation
- Systematic review of multi-agent RAG for clinical decision support in low-resource contexts

### Similar Projects
- datalaw.bot — DS-I Africa Law project using GPT-4o (12 African countries)
- datalaw.africa — DTA/MTA resources and templates

### Source Documents
- POPIA: https://popia.co.za/
- Kenya DPA: https://www.interior.go.ke/sites/default/files/2024-09/27.%20Data%20Protection%20Act%202019.pdf
- Uganda DPPA: https://ict.go.ug/wp-content/uploads/2019/03/Data-Protection-and-Privacy-Act-2019.pdf
- Malabo Convention: https://ccdcoe.org/uploads/2018/11/AU-270614-CSConvention.pdf

---

*This specs sheet was developed through collaborative ideation between Atwine and Claude, based on requirements gathered from the ABI CoP AI meeting email thread (May-June 2026).*
