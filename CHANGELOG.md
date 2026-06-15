# Changelog

All notable changes to PolicyLens will be documented in this file.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) conventions.  
Version numbers follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

> Features planned for post-MVP development. See [Roadmap](README.md#roadmap-post-mvp) in README.

- Streaming agent log updates within Streamlit using `graph.stream()`
- Additional African country documents (Rwanda, Tanzania, Ghana, Zimbabwe)
- Side-by-side clause comparison view in the UI
- Citation linking — click a citation to jump to the source PDF page
- Hugging Face Spaces deployment for remote Community of Practice access
- DTA/MTA draft generation based on applicable jurisdiction requirements
- French-language document support for Francophone African laws
- Parallel sub-question retrieval for faster pipeline execution

---

## [0.1.0] — 2026-06-15

**MVP release.** First working end-to-end agentic RAG pipeline for African data protection law analysis. Demonstrated full Plan → Retrieve → Evaluate → Rewrite → Synthesize flow on 5 legal documents across 5 jurisdictions.

### Added

#### Core Pipeline
- `config.py` — central configuration file; single source of truth for all model names, paths, chunk settings, and demo questions
- `ingest.py` — document ingestion pipeline: PDF text extraction (pdfplumber), section detection, overlapping chunking (RecursiveCharacterTextSplitter), embedding via nomic-embed-text (Ollama), storage in ChromaDB with full metadata tagging
- `retrieval.py` — ChromaDB search utilities with country-level metadata filtering (`search_by_country`, `search_all`, `format_context`)
- `nodes.py` — six LangGraph node functions implementing the full agentic pipeline:
  - `plan_node` — LLM-driven research planner; produces structured JSON sub-questions per country
  - `retrieve_node` — ChromaDB vector search with country metadata filter
  - `evaluate_node` — LLM sufficiency checker; returns SUFFICIENT / INSUFFICIENT verdict with reasoning
  - `rewrite_node` — LLM query rewriter; generates alternative legal terminology when context is insufficient
  - `advance_node` — state manager; advances to next sub-question and resets retry counter
  - `synthesize_node` — LLM synthesizer; produces formal, cited legal analysis from all retrieved context
- `graph.py` — LangGraph `StateGraph` wiring all nodes with conditional edges for the retry loop and sub-question iteration; `run_query()` public entry point
- `app.py` — Streamlit frontend with custom CSS, sidebar, preset question buttons, live agent log display, metrics bar (sub-questions / searches / rewrites), styled answer card, and download button

#### Prompt Files (`prompts/`)
- `planner.txt` — instructs LLM to output valid JSON sub-questions with country assignments; limits to 5 sub-questions
- `evaluator.txt` — strict sufficiency checking; requires SUFFICIENT/INSUFFICIENT as first word with reasoning
- `rewriter.txt` — legal synonym substitution guide (e.g. "cross-border transfer" → "transborder flow of personal information")
- `synthesizer.txt` — formal legal research assistant persona; citation requirements; structured format rules for comparison, compliance, and gap-analysis question types

#### Knowledge Base (5 documents, 442 chunks)
- `docs/south_africa_popia.pdf` — Protection of Personal Information Act (POPIA), 2013 · 76 pages · 182 chunks
- `docs/kenya_dpa_2019.pdf` — Data Protection Act No. 24 of 2019 · 35 pages · 64 chunks
- `docs/Nigeria_Data_Protection_Act_2023.pdf` — Nigeria Data Protection Act, 2023 · 43 pages · 78 chunks
- `docs/botswana.pdf` — Data Protection Act, 2018 (Botswana) · 21 pages · 40 chunks
- `docs/au_malabo_convention.pdf` — AU Malabo Convention on Cyber Security and Personal Data Protection, 2014 · 40 pages · 78 chunks

#### Documentation
- `README.md` — comprehensive README with badges, architecture diagram, setup guide, usage instructions, configuration reference, known limitations, and roadmap
- `CHANGELOG.md` — this file
- `requirements.txt` — pinned Python dependencies

#### UI / UX
- Custom CSS theming in `app.py`: dark hero header, sidebar with knowledge base overview and pipeline explanation, styled preset question buttons, dark terminal-style agent log panel, answer card with shadow, download button
- Agent activity log with colour-coded step indicators (📋 plan / 🔍 search / ✅ sufficient / ⚠️ insufficient / 🔄 rewrite / 📝 synthesize)
- Metrics bar showing sub-question count, total searches run, and query rewrites triggered per session

#### Console Instrumentation (`nodes.py`)
- Real-time `print()` output to terminal at every agent step: planner reasoning, per-passage relevance scores and section headings, evaluator verdict and reasoning preview, rewriter output, advance transitions, synthesizer summary

### Fixed

- **Windows stdout encoding** — added `sys.stdout.reconfigure(encoding='utf-8', errors='replace')` to `ingest.py` and `$env:PYTHONIOENCODING="utf-8"` to run commands; prevents `OSError: [Errno 22] Invalid argument` on emoji characters in Windows console
- **Ollama connection** — `langchain_ollama` defaults to a different host than the running Ollama service; fixed by passing `base_url=OLLAMA_BASE_URL` explicitly to all `OllamaEmbeddings` and `ChatOllama` instantiations in `ingest.py`, `retrieval.py`, and `nodes.py`
- **Sufficiency check logic** — corrected evaluator verdict parsing: `"SUFFICIENT" in answer and "INSUFFICIENT" not in answer` prevents false-positive SUFFICIENT matches when the LLM outputs "INSUFFICIENT"

### Removed

- **Uganda DPPA 2019** (`uganda_dppa_2019.pdf`) — original PDF confirmed to be a 32-page scanned image with no text layer; zero text extractable by pdfplumber or PyMuPDF. Replaced with Nigeria NDPA 2023 and Botswana DPA 2018, both fully text-based

### Changed

- Demo question 2 updated from "South Africa and Uganda" to "South Africa, Nigeria, and Botswana" following Uganda document removal
- Demo question 3 updated to reference Nigeria instead of Uganda
- `prompts/planner.txt` updated: replaced "Uganda" with "Nigeria, Botswana" in the available countries list

### Dependencies

| Package | Version |
|---|---|
| langgraph | 1.2.5 |
| langchain | 1.3.9 |
| langchain-ollama | 1.1.0 |
| langchain-chroma | 1.1.0 |
| langchain-core | 1.4.7 |
| langchain-text-splitters | 1.1.2 |
| chromadb | 1.5.9 |
| pdfplumber | 0.11.9 |
| streamlit | 1.58.0 |
| numpy | 2.4.6 |

---

## [0.0.1] — 2026-06-14

**Project initialisation.** Specs sheet written, folder structure created, virtual environment set up.

### Added
- `agentic_rag_specs.md` — full architecture specification, tech stack decisions, prompt guidelines, file-by-file implementation plan, hardware requirements, and demo questions
- Project folder structure: `docs/`, `chroma_db/`, `prompts/`
- Python 3.12.6 virtual environment (`venv/`)
- Ollama models confirmed available: `llama3.1:8b`, `nomic-embed-text:latest`
- Source PDFs obtained: South Africa POPIA, Kenya DPA 2019, AU Malabo Convention

---

[Unreleased]: https://github.com/atwine/Africa-Policy-Lens/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/atwine/Africa-Policy-Lens/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/atwine/Africa-Policy-Lens/releases/tag/v0.0.1
