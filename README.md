# PolicyLens — African Data Protection Policy Assistant

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![vLLM](https://img.shields.io/badge/vLLM-Llama%203.3%2070B-1a1a2e?style=for-the-badge&logo=nvidia&logoColor=white)](https://docs.vllm.ai/)
[![Ollama](https://img.shields.io/badge/Ollama-nomic--embed--text-black?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2.5-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-1.5.9-FF6719?style=for-the-badge&logo=databricks&logoColor=white)](https://www.trychroma.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.58.0-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![ACE HPC](https://img.shields.io/badge/Compute-ACE%20HPC%20A100%2080GB-76B900?style=for-the-badge&logo=nvidia&logoColor=white)]()
[![Status](https://img.shields.io/badge/Status-MVP%20v0.1-orange?style=for-the-badge)]()

> **MVP v0.1** · Target Demo: July 2, 2026 — ABI AI Community of Practice Meeting  
> Author: Mugume Twinamatsiko Atwine · ML Engineer / Data Scientist, ACE, IDI Kampala

---

## Screenshot

![PolicyLens User Interface](images/User%20Interface.png)

*The PolicyLens UI — preset question buttons on the left, agent activity log and formal analysis on the right.*

---

## What Is This?

PolicyLens is an **agentic RAG (Retrieval-Augmented Generation)** tool that answers complex, multi-jurisdiction questions about African data protection laws and related policy/governance frameworks.

Unlike standard RAG (one search → one answer), PolicyLens uses a **three-stage agentic pipeline**:

1. **Planner** — breaks your question into targeted sub-questions, one per country or policy scope
2. **Retriever + Evaluator** — searches documents per scope, then checks whether retrieved passages actually answer the sub-question. If not, it rewrites the query using alternative legal terminology and retries (up to 2 times)
3. **Synthesizer** — combines all retrieved context into a single, formally structured answer with specific section citations

This approach handles questions that require reasoning across multiple countries' laws simultaneously — something vanilla RAG cannot do reliably.

> **Compute split:** The reasoning LLM runs on a remote **ACE HPC A100 80GB** via vLLM; embeddings stay local on **Ollama** (`nomic-embed-text`). No cloud API keys are required.

---

## Why Agentic RAG for Legal Policy?

Standard RAG fails on legal questions because:

| Problem | Example | Standard RAG | Agentic RAG |
|---|---|---|---|
| Terminology mismatch | User says "data sharing", law says "transborder flow of personal information" | Misses the relevant clause | Rewrites query with legal synonyms |
| Multi-country questions | "Compare South Africa and Kenya on cross-border transfer rules" | Returns a mix of passages, no structure | Plans one sub-question per country, retrieves separately |
| Insufficient context | A single search returns general principles but not specific conditions | Answers anyway (hallucination risk) | Detects insufficiency and retries |

---

## Knowledge Base (17 Documents, 1,450 Chunks)

![chunks](https://img.shields.io/badge/Total%20Chunks-1450-0ea5e9?style=flat-square)
![docs](https://img.shields.io/badge/Source%20Documents-17-6366f1?style=flat-square)
![countries](https://img.shields.io/badge/Scopes-13-14b8a6?style=flat-square)

### Binding laws

| Country | Law | Chunks |
|---|---|---|
| 🇿🇦 South Africa | Protection of Personal Information Act (POPIA), 2013 | 182 |
| 🇰🇪 Kenya | Data Protection Act No. 24 of 2019 | 64 |
| 🇳🇬 Nigeria | Nigeria Data Protection Act (NDPA), 2023 | 78 |
| 🇧🇼 Botswana | Data Protection Act, 2018 | 40 |
| 🇸🇿 Eswatini | Data Protection Act, 2022 | 60 |
| 🇿🇼 Zimbabwe | Data Protection Act [Chapter 11:12], 2021 | 81 |
| 🌍 African Union | Malabo Convention on Cyber Security and Personal Data Protection, 2014 | 78 |

### Policy & governance documents

| Scope | Document | Chunks |
|---|---|---|
| African Union | Digital Transformation Strategy for Africa (2020–2030) | 141 |
| African Union | Continental Artificial Intelligence Strategy, July 2024 | 152 |
| African Union | Science, Technology and Innovation Strategy (STISA 2034), 2025–2034 | 82 |
| African Union | Data Policy Framework, 2022 | 221 |
| EU-Africa | PerMed Policy Brief No. 2 — Personalised Medicine Collaboration, January 2025 | 27 |
| OECD | Facilitating the Secondary Use of Health Data for Public Interest Purposes Across Borders, June 2025 | 118 |
| Pathogen Data Network | Data Publishing Policy Version 2, June 2025 | 4 |
| SADC | Cyber-Infrastructure Framework, June 2016 | 38 |
| Wellcome Trust | Tackling Pathogen Genomic Sequence Data Sharing Challenges, 2025 | 42 |
| International | Thaldar et al. — Communicating clearly about data sharing in genomics (Human Genomics, 2025) | 42 |

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
│  sub-questions, one per scope       │
└───────────────┬─────────────────────┘
                │  sub-questions[]
                ▼
┌─────────────────────────────────────┐  ◄─────────────────────┐
│  STAGE 2: RETRIEVER                 │                        │
│  ChromaDB search (scope filter)     │                        │
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

| Component | Technology | Notes |
|---|---|---|
| LLM (reasoning) | Llama 3.3 70B Instruct AWQ | vLLM on ACE HPC A100 80GB |
| Embeddings | nomic-embed-text | Ollama (local) |
| Vector store | ChromaDB | Local persistent |
| Orchestration | LangGraph | 1.2.5 |
| LangChain integrations | langchain-openai / langchain-ollama / langchain-chroma | — |
| Document parsing | pdfplumber | 0.11.9 |
| Frontend | Streamlit | 1.58.0 |
| Runtime | Python | 3.12.6 |

---

## Project Structure

```
PolicyBot/
│
├── README.md                 ← You are here
├── requirements.txt          ← Python dependencies
├── config.py                 ← All settings (models, paths, documents, demo questions)
├── ingest.py                 ← Run once: loads PDFs into ChromaDB
├── download_docs.py          ← Download source PDFs from policy_download_list.md
├── retrieval.py              ← ChromaDB search utilities with metadata filtering
├── nodes.py                  ← LangGraph node functions (plan, retrieve, evaluate, rewrite, synthesize, follow-up)
├── graph.py                  ← LangGraph flow wiring + run_query() entry point
├── app.py                    ← Streamlit UI (two tabs: About + PolicyLens)
│
├── prompts/
│   ├── planner.txt           ← System prompt for Stage 1 (research planning)
│   ├── evaluator.txt         ← System prompt for Stage 2 (sufficiency checking)
│   ├── rewriter.txt          ← System prompt for Stage 2 (query rewriting with legal synonyms)
│   ├── synthesizer.txt       ← System prompt for Stage 3 (formal answer generation)
│   └── follow_up_generator.txt ← System prompt for Stage 4 (follow-up question suggestions)
│
├── docs/                     ← Source PDF documents
│   ├── south_africa_popia.pdf
│   ├── kenya_dpa_2019.pdf
│   ├── Nigeria_Data_Protection_Act_2023.pdf
│   ├── botswana.pdf
│   ├── eswatini.pdf
│   ├── zimbabwe1.pdf
│   ├── au_malabo_convention.pdf
│   └── policy_governance/    ← Policy/governance PDFs
│
├── docs/future/              ← Continental/regional frameworks for future ingestion
├── docs/reference/           ← Research papers for reference
├── chroma_db/                ← ChromaDB persistent storage (auto-created by ingest.py)
└── sessions/                 ← Saved query results (auto-created by app.py)
```

---

## Setup — First Time

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/download) installed and running locally (for embeddings only)
- Network access to the ACE HPC vLLM endpoint configured in `config.py`

### 1. Pull the required Ollama embedding model

```bash
ollama pull nomic-embed-text   # Embedding model (~274 MB)
```

Verify it is available:

```bash
ollama list
# Expected output includes:
# nomic-embed-text:latest
```

### 2. Clone / download this project

```
C:\Users\ic\OneDrive\Desktop\PolicyBot\
```

### 3. Place the source PDFs

You can either:

- **Use the existing documents** already in `docs/` and `docs/policy_governance/`, or
- **Download the full curated list** from `docs/policy_download_list.md`:

```bash
python download_docs.py
```

The script creates `docs/future/` and `docs/reference/` as needed, skips files that already exist, and verifies each download starts with `%PDF`.

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
  African Union : 674 chunks
  Botswana      : 40 chunks
  ...
  TOTAL         : 1450 chunks
```

---

## Running the App

```bash
# Make sure Ollama is running locally (for embeddings), then:
cd "C:\Users\ic\OneDrive\Desktop\PolicyBot"
venv\Scripts\activate
streamlit run app.py
```

Opens at: **http://localhost:8501**

The app opens on the **About** tab by default, which explains the project, lists the knowledge base, and shows the 4 preset demo questions. Switch to the **PolicyLens** tab to run questions.

---

## Using the UI

### Two-tab layout

- **About** — project overview, knowledge base table, sample questions, how it works, tech stack
- **PolicyLens** — the interactive question + analysis interface

### Preset Demo Buttons

Four buttons aligned with the ABI demo priorities:

| Button | Type | Scopes |
|---|---|---|
| 🔀 Compare SA & Kenya | Alignment / conflict analysis | South Africa, Kenya, AU |
| 🏥 Health data: SA & Nigeria | Compliance checklist | South Africa, Nigeria |
| 🌍 Multi-country gap analysis | Gap identification | South Africa, Kenya, Nigeria |
| 🏛️ National vs AU Malabo | Comparative framework | All + African Union |

### Custom Questions

Type any question in the text box and click **Ask PolicyLens**. Questions that reference scopes outside the knowledge base trigger a broad search across all available documents.

### Follow-up Questions
After each analysis, PolicyLens generates 3–5 logical follow-up questions (causal, comparative, gap, or implementation angles). Click any suggestion to run it through the pipeline and see the new answer.

### Agent Activity Log

The left panel shows exactly what the agents are doing:

- 📋 Planning step — sub-questions and reasoning
- 🔍 Each ChromaDB search with passage count
- ✅ / ⚠️ Evaluator verdict per sub-question
- 🔄 Query rewrites (when triggered)
- 📝 Synthesis step

### Metrics Bar

Below the log: number of sub-questions generated, total searches run, and query rewrites triggered.

### Download

The analysis panel includes a **Download analysis as .txt** button for saving answers.

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
# vLLM endpoint (ACE HPC)
VLLM_BASE_URL = "http://10.35.50.41:8000/v1"
LLM_MODEL = "ibnzterrell/Meta-Llama-3.3-70B-Instruct-AWQ-INT4"

# Local Ollama embeddings
OLLAMA_BASE_URL = "http://localhost:11434"
EMBEDDING_MODEL = "nomic-embed-text"

# Retrieval depth
TOP_K = 5                          # chunks returned per search
MAX_RETRIES = 2                    # max query rewrites per sub-question

# Chunk size (re-run ingest.py after changing)
CHUNK_SIZE_CHARS = 1500
CHUNK_OVERLAP_CHARS = 200
```

### Adding a New Country / Document

1. Place the PDF (text-based, not scanned) in `docs/` or a subdirectory
2. Add an entry to `DOCUMENTS` in `config.py`:
   ```python
   "filename.pdf": {
       "country": "Country or Scope Name",
       "document_type": "binding_law",  # or "continental_strategy", "policy_brief", etc.
       "document_name": "Full Document Name, Year",
       "source_dir": "docs/subdir"      # optional, defaults to "docs/"
   }
   ```
3. Update `prompts/planner.txt` — add the scope to the "Available countries and scopes" line
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
| `planner.txt` | How sub-questions are generated; which scopes to consider |
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
- **LLM response time** — the 70B model on the remote vLLM server takes 30–90 seconds per full pipeline run depending on question complexity and network latency.
- **No streaming within Streamlit** — the process log appears all at once after the pipeline completes (LangGraph runs synchronously). Real-time streaming requires a streaming-aware graph implementation.
- **ChromaDB metadata filtering** — requires exact scope name match. Typos in questions ("South Africa" vs "S. Africa") are handled by the planner, not the retriever.
- **English only** — all source documents are in English; the system does not support French-language documents (e.g., some Francophone African laws).

---

## Roadmap (Post-MVP)

![planned](https://img.shields.io/badge/Status-Post--MVP%20Planning-8b5cf6?style=flat-square)

- [ ] Add more African countries as text-based PDFs become available (Rwanda, Tanzania, Ghana)
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
