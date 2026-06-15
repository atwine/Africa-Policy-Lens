# PolicyLens — African Data Protection Policy Assistant

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Ollama](https://img.shields.io/badge/Ollama-Llama%203.1%208B-black?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2.5-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-1.5.9-FF6719?style=for-the-badge&logo=databricks&logoColor=white)](https://www.trychroma.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.58.0-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Local Only](https://img.shields.io/badge/Runs-100%25%20Locally-22c55e?style=for-the-badge&logo=homeassistant&logoColor=white)]()
[![No API Keys](https://img.shields.io/badge/API%20Keys-None%20Required-22c55e?style=for-the-badge&logo=opensourceinitiative&logoColor=white)]()
[![GPU](https://img.shields.io/badge/GPU-RTX%203050%206GB-76B900?style=for-the-badge&logo=nvidia&logoColor=white)]()
[![License](https://img.shields.io/badge/License-Research%20Use-blue?style=for-the-badge)]()
[![Status](https://img.shields.io/badge/Status-MVP%20v0.1-orange?style=for-the-badge)]()

> **MVP v0.1** · Target Demo: July 2, 2026 — ABI AI Community of Practice Meeting  
> Author: Mugume Twinamatsiko Atwine · ML Engineer / Data Scientist, ACE, IDI Kampala

---

## Screenshot

![PolicyLens User Interface](images/User%20Interface.png)

*The PolicyLens UI — preset question buttons on the left, agent activity log and formal analysis on the right.*

---

## What Is This?

PolicyLens is a **locally-run agentic RAG (Retrieval-Augmented Generation) tool** that answers complex, multi-jurisdiction questions about African data protection laws.

Unlike standard RAG (one search → one answer), PolicyLens uses a **three-stage agentic pipeline**:

1. **Planner** — breaks your question into targeted sub-questions, one per country
2. **Retriever + Evaluator** — searches legal documents per country, then checks whether retrieved passages actually answer the sub-question. If not, it rewrites the query using alternative legal terminology and retries (up to 2 times)
3. **Synthesizer** — combines all retrieved context into a single, formally structured answer with specific section citations

This approach handles questions that require reasoning across multiple countries' laws simultaneously — something vanilla RAG cannot do reliably.

---

## Why Agentic RAG for Legal Policy?

Standard RAG fails on legal questions because:

| Problem | Example | Standard RAG | Agentic RAG |
|---|---|---|---|
| Terminology mismatch | User says "data sharing", law says "transborder flow of personal information" | Misses the relevant clause | Rewrites query with legal synonyms |
| Multi-country questions | "Compare South Africa and Kenya on cross-border transfer rules" | Returns a mix of passages, no structure | Plans one sub-question per country, retrieves separately |
| Insufficient context | A single search returns general principles but not specific conditions | Answers anyway (hallucination risk) | Detects insufficiency and retries |

---

## Knowledge Base (5 Documents, 442 Chunks)

![chunks](https://img.shields.io/badge/Total%20Chunks-442-0ea5e9?style=flat-square)
![docs](https://img.shields.io/badge/Source%20Documents-5-6366f1?style=flat-square)
![countries](https://img.shields.io/badge/Countries-4%20%2B%20AU-14b8a6?style=flat-square)

| Country | Law | Chunks |
|---|---|---|
| 🇿🇦 South Africa | Protection of Personal Information Act (POPIA), 2013 | ![182](https://img.shields.io/badge/182%20chunks-1d4ed8?style=flat-square) |
| 🇰🇪 Kenya | Data Protection Act No. 24 of 2019 | ![64](https://img.shields.io/badge/64%20chunks-1d4ed8?style=flat-square) |
| 🇳🇬 Nigeria | Nigeria Data Protection Act (NDPA), 2023 | ![78](https://img.shields.io/badge/78%20chunks-1d4ed8?style=flat-square) |
| 🇧🇼 Botswana | Data Protection Act, 2018 | ![40](https://img.shields.io/badge/40%20chunks-1d4ed8?style=flat-square) |
| 🌍 African Union | Malabo Convention on Cyber Security and Personal Data Protection, 2014 | ![78](https://img.shields.io/badge/78%20chunks-1d4ed8?style=flat-square) |

Each chunk carries structured metadata: `country`, `document_name`, `document_type`, `section_heading`, `start_page`, `end_page`, `chunk_index`.

---

## Architecture

```
User Question
      │
      ▼
┌─────────────────────────────────────┐
│  STAGE 1: PLANNER                   │
│  LLM breaks question into           │
│  sub-questions, one per country     │
└───────────────┬─────────────────────┘
                │  sub-questions[]
                ▼
┌─────────────────────────────────────┐  ◄─────────────────────┐
│  STAGE 2: RETRIEVER                 │                        │
│  ChromaDB search (country filter)   │                        │
│  → top-5 relevant chunks            │                        │
└───────────────┬─────────────────────┘                        │
                │                                              │
                ▼                                              │
┌─────────────────────────────────────┐                        │
│  STAGE 2: EVALUATOR                 │  INSUFFICIENT          │
│  "Is this enough to answer the      ├────────────────────────┤
│   sub-question?" SUFFICIENT /        │  (max 2 retries)       │
│   INSUFFICIENT                      │                        │
└───────────────┬─────────────────────┘       ┌───────────────┤
                │ SUFFICIENT                   │  REWRITER     │
                │                              │  Rewrites     │
                ▼                              │  query with   │
         [Next sub-question] ─────────────────►│  legal        │
         or                                   │  synonyms     │
         [All done]                            └───────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│  STAGE 3: SYNTHESIZER               │
│  Combines all context, generates    │
│  formal answer with section cites   │
└───────────────┬─────────────────────┘
                │
                ▼
        Final Answer (UI)
```

---

## Tech Stack

| Component | Technology | Version |
|---|---|---|
| LLM (reasoning) | ![Ollama](https://img.shields.io/badge/Llama%203.1%208B-Ollama-black?style=flat-square&logo=ollama) | — |
| Embeddings | ![nomic](https://img.shields.io/badge/nomic--embed--text-Ollama-black?style=flat-square&logo=ollama) | — |
| Vector store | ![ChromaDB](https://img.shields.io/badge/ChromaDB-local%20persistent-FF6719?style=flat-square) | 1.5.9 |
| Orchestration | ![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C?style=flat-square&logo=langchain) | 1.2.5 |
| LangChain integrations | ![LangChain](https://img.shields.io/badge/langchain--ollama%20%2F%20langchain--chroma-1C3C3C?style=flat-square&logo=langchain) | 1.1.0 / 1.1.0 |
| Document parsing | ![pdfplumber](https://img.shields.io/badge/pdfplumber-PDF%20text%20extraction-red?style=flat-square) | 0.11.9 |
| Frontend | ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white) | 1.58.0 |
| Runtime | ![Python](https://img.shields.io/badge/Python-3.12.6-3776AB?style=flat-square&logo=python&logoColor=white) | 3.12.6 |

> ![Local](https://img.shields.io/badge/Runs-100%25%20Locally-22c55e?style=flat-square&logo=homeassistant&logoColor=white) &nbsp; ![NoKeys](https://img.shields.io/badge/No%20Cloud%20API%20Keys-Required-22c55e?style=flat-square&logo=opensourceinitiative&logoColor=white)

---

## Hardware Requirements

| Resource | Minimum | This Machine |
|---|---|---|
| GPU VRAM | 6 GB | NVIDIA RTX 3050 (6 GB) |
| System RAM | 16 GB | 24 GB DDR5 |
| Storage | 10 GB free | NVMe SSD |
| CUDA | 11.8+ | 12.7 |
| OS | Windows 10/11 or Linux | Windows |

---

## Project Structure

```
PolicyBot/
│
├── README.md                 ← You are here
├── requirements.txt          ← Python dependencies
├── config.py                 ← All settings (models, paths, documents, demo questions)
├── ingest.py                 ← Run once: loads PDFs into ChromaDB
├── retrieval.py              ← ChromaDB search utilities with metadata filtering
├── nodes.py                  ← LangGraph node functions (plan, retrieve, evaluate, rewrite, synthesize)
├── graph.py                  ← LangGraph flow wiring + run_query() entry point
├── app.py                    ← Streamlit UI
│
├── prompts/
│   ├── planner.txt           ← System prompt for Stage 1 (research planning)
│   ├── evaluator.txt         ← System prompt for Stage 2 (sufficiency checking)
│   ├── rewriter.txt          ← System prompt for Stage 2 (query rewriting with legal synonyms)
│   └── synthesizer.txt       ← System prompt for Stage 3 (formal answer generation)
│
├── docs/                     ← Source PDF documents (place here before ingesting)
│   ├── south_africa_popia.pdf
│   ├── kenya_dpa_2019.pdf
│   ├── Nigeria_Data_Protection_Act_2023.pdf
│   ├── botswana.pdf
│   └── au_malabo_convention.pdf
│
└── chroma_db/                ← ChromaDB persistent storage (auto-created by ingest.py)
```

---

## Setup — First Time

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/download) installed and running

### 1. Pull the required Ollama models

```bash
ollama pull llama3.1:8b        # Main reasoning model (~4.7 GB)
ollama pull nomic-embed-text   # Embedding model (~274 MB)
```

Verify they are available:

```bash
ollama list
# Expected output includes:
# llama3.1:8b
# nomic-embed-text:latest
```

### 2. Clone / download this project

```
C:\Users\ic\OneDrive\Desktop\PolicyBot\
```

### 3. Place the source PDFs in `docs/`

The following files must be present (text-based PDFs only — scanned image PDFs will not work):

```
docs/south_africa_popia.pdf
docs/kenya_dpa_2019.pdf
docs/Nigeria_Data_Protection_Act_2023.pdf
docs/botswana.pdf
docs/au_malabo_convention.pdf
```

### 4. Create and activate a virtual environment

```bash
cd "C:\Users\ic\OneDrive\Desktop\PolicyBot"
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Run the ingestion pipeline (once)

```bash
python ingest.py
```

Expected output:
```
============================================================
PolicyLens — Document Ingestion Pipeline
============================================================

Processing: south_africa_popia.pdf
  Extracted 76 pages
  Detected 76 sections
  Generated 182 chunks
...
INGESTION SUMMARY
  African Union : 78 chunks
  Botswana      : 40 chunks
  Kenya         : 64 chunks
  Nigeria       : 78 chunks
  South Africa  : 182 chunks
  TOTAL         : 442 chunks
```

---

## Running the App

```bash
# Make sure Ollama is running, then:
cd "C:\Users\ic\OneDrive\Desktop\PolicyBot"
venv\Scripts\activate
streamlit run app.py
```

Opens at: **http://localhost:8501**

---

## Using the UI

![PolicyLens User Interface](images/User%20Interface.png)

### Preset Demo Buttons
Four buttons covering the main question types:

| Button | Type | Countries |
|---|---|---|
| 🔀 Compare SA & Kenya | Alignment / conflict analysis | South Africa, Kenya, AU |
| 🏥 Compliance: SA, Nigeria & Botswana | Requirements checklist | South Africa, Nigeria, Botswana |
| 🌍 Multi-country gap analysis | Gap identification | South Africa, Kenya, Nigeria |
| 🏛️ National vs AU Malabo | Comparative framework | All + African Union |

### Custom Questions
Type any question in the text box and click **Ask PolicyLens**. Questions that reference countries outside the knowledge base will trigger a broad search across all available documents.

### Agent Activity Log
The left panel shows exactly what the agents are doing in real time:
- 📋 Planning step — sub-questions and reasoning
- 🔍 Each ChromaDB search with passage count
- ✅ / ⚠️ Evaluator verdict per sub-question
- 🔄 Query rewrites (when triggered)
- 📝 Synthesis step

### Metrics Bar
Below the log: number of sub-questions generated, total searches run, and query rewrites triggered.

### Download
The analysis panel includes a **Download as .txt** button for saving answers.

---

## Console Output (Terminal)

When running via `streamlit run app.py` or the test script, the terminal shows verbose real-time output from every agent step:

```
============================================================
[STAGE 1] PLANNER
============================================================
  Question: Where do the data protection laws of South Africa and Kenya align...
  Reasoning: This question requires comparing two countries' positions...
  Identified 3 sub-question(s):
    1. [South Africa] What are the conditions for cross-border transfer...
    2. [Kenya] What are the conditions for cross-border transfer...
    3. [African Union] How do the Malabo Convention provisions apply...

[STAGE 2 — Sub-question 1/3] RETRIEVER
  Country filter : South Africa
  Search query   : What are the conditions for cross-border transfer...
  Retrieved      : 5 passages
    Passage 1: relevance=0.821 | section='Chapter 9 — Transborder...' | pages 48-50

  [EVALUATOR] Verdict: SUFFICIENT

  [ADVANCE] Sub-question 1 complete. Moving to sub-question 2/3
...
============================================================
[STAGE 3] SYNTHESIZER
============================================================
  Answer generated (2847 chars).
```

---

## Configuration

All settings live in `config.py`. Common things to change:

```python
# Switch LLM model
LLM_MODEL = "llama3.1:8b"        # or "llama3.2:3b" for faster/lighter responses

# Retrieval depth
TOP_K = 5                          # chunks returned per search
MAX_RETRIES = 2                    # max query rewrites per sub-question

# Chunk size (re-run ingest.py after changing)
CHUNK_SIZE_CHARS = 1500
CHUNK_OVERLAP_CHARS = 200
```

### Adding a New Country / Document

1. Place the PDF (text-based, not scanned) in `docs/`
2. Add an entry to `DOCUMENTS` in `config.py`:
   ```python
   "filename.pdf": {
       "country": "Country Name",
       "document_type": "binding_law",
       "document_name": "Full Law Name, Year"
   }
   ```
3. Update `prompts/planner.txt` — add the country name to the "Available countries" line
4. Clear the existing ChromaDB and re-run ingestion:
   ```bash
   Remove-Item -Recurse chroma_db\*   # Windows PowerShell
   python ingest.py
   ```

---

## Prompt Files

Prompts live in `prompts/` as plain `.txt` files — edit them directly to tune behaviour without touching Python code.

| File | Controls |
|---|---|
| `planner.txt` | How sub-questions are generated; which countries to consider |
| `evaluator.txt` | How strict the sufficiency check is |
| `rewriter.txt` | Legal synonym substitutions for query rewriting |
| `synthesizer.txt` | Answer format, citation style, persona |

---

## Known Limitations (MVP)

![scanned](https://img.shields.io/badge/Scanned%20PDFs-Not%20Supported-ef4444?style=flat-square)
![streaming](https://img.shields.io/badge/Live%20Streaming-Not%20Yet-f59e0b?style=flat-square)
![english](https://img.shields.io/badge/Language-English%20Only-f59e0b?style=flat-square)
![latency](https://img.shields.io/badge/Response%20Time-30--90s-f59e0b?style=flat-square)

- **Scanned PDFs not supported** — documents must have a text layer. The original Uganda DPPA 2019 PDF was image-only and had to be replaced.
- **LLM response time** — Llama 3.1 8B on a 6 GB GPU takes 30–90 seconds per full pipeline run depending on question complexity.
- **No streaming within Streamlit** — the process log appears all at once after the pipeline completes (LangGraph runs synchronously). Real-time streaming requires a streaming-aware graph implementation.
- **ChromaDB metadata filtering** — requires exact country name match. Typos in questions ("South Africa" vs "S. Africa") are handled by the planner, not the retriever.
- **English only** — all source documents are in English; the system does not support French-language documents (e.g., some Francophone African laws).

---

## Roadmap (Post-MVP)

![planned](https://img.shields.io/badge/Status-Post--MVP%20Planning-8b5cf6?style=flat-square)

- [ ] Add more African countries as text-based PDFs become available (Rwanda, Tanzania, Ghana, Zimbabwe)
- [ ] Streaming log updates within Streamlit using `graph.stream()`
- [ ] Side-by-side clause comparison view
- [ ] Citation linking — click a citation to open the source PDF at that page
- [ ] Hugging Face Spaces deployment for remote CoP access
- [ ] DTA/MTA draft generation — generate Data Transfer Agreement clauses based on applicable laws
- [ ] French-language document support
- [ ] Parallel sub-question retrieval for faster responses

---

## References

### Architecture
- Google Research: [Unlocking Dependable Responses with Gemini Enterprise Agent Platforms: Agentic RAG](https://research.google/blog/unlocking-dependable-responses-with-gemini-enterprise-agent-platforms-agentic-rag/)

### Academic
- MA-RAG: Multi-Agent RAG via Collaborative Chain-of-Thought Reasoning (2024)
- HM-RAG: Hierarchical Multi-Agent RAG (12.95% accuracy improvement via multi-source retrieval)
- MAO-ARAG: Adaptive Agentic RAG with iterative context evaluation

### Related Projects
- [datalaw.bot](https://datalaw.bot) — DS-I Africa Law project (12 African countries, GPT-4o)
- [datalaw.africa](https://datalaw.africa) — DTA/MTA resources and templates

### Source Documents
- POPIA: https://popia.co.za/
- Kenya DPA: https://www.interior.go.ke/sites/default/files/2024-09/27.%20Data%20Protection%20Act%202019.pdf
- Nigeria NDPA: https://fccpc.gov.ng
- Malabo Convention: https://ccdcoe.org/uploads/2018/11/AU-270614-CSConvention.pdf

