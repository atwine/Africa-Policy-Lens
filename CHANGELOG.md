# Changelog

All notable changes to PolicyLens will be documented in this file.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) conventions.  
Version numbers follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

> Features planned for post-MVP development. See [Roadmap](README.md#roadmap-post-mvp) in README.

- Streaming agent log updates within Streamlit using `graph.stream()`
- Additional African country documents (Rwanda, Tanzania, Ghana)
- Side-by-side clause comparison view in the UI
- Citation linking — click a citation to jump to the source PDF page
- Hugging Face Spaces deployment for remote Community of Practice access
- DTA/MTA draft generation based on applicable jurisdiction requirements
- French-language document support for Francophone African laws
- Parallel sub-question retrieval for faster pipeline execution
- Conversation threading — accumulate follow-up answers below previous answers and download the full thread as one file

---

## [0.1.3] — 2026-07-01

### Added

- **vLLM / A100 backend** — migrated the reasoning LLM from local Ollama (`llama3.1:8b`) to a remote vLLM server running `ibnzterrell/Meta-Llama-3.3-70B-Instruct-AWQ-INT4` on ACE HPC (A100 80GB). Embeddings remain local via Ollama (`nomic-embed-text`) (`config.py`, `nodes.py`, `requirements.txt`, `README.md`)
- **Policy & governance documents** — ingested 4 new AU strategy/policy PDFs into the knowledge base: Digital Transformation Strategy (2020–2030), Continental AI Strategy (July 2024), STISA 2034 (2025–2034), and Data Policy Framework (2022) (`config.py`, `ingest.py`, `prompts/planner.txt`)
- **Two-tab Streamlit UI** — split `app.py` into an **About** tab (project overview, knowledge base table, sample questions, tech stack) and a **PolicyLens** tab (the interactive question interface)
- **Follow-up question generator** — new `follow_up_node` in the LangGraph pipeline that generates 3–5 logical follow-up questions from the final answer; displayed as clickable buttons below the analysis in `app.py` (`prompts/follow_up_generator.txt`, `nodes.py`, `graph.py`, `app.py`)
- **PDF download script** — `download_docs.py` parses `docs/policy_download_list.md`, downloads all listed PDFs into the correct directories, skips existing valid files, verifies PDF headers, and supports `--no-verify-ssl` for self-signed certificates (`download_docs.py`, `requirements.txt`, `docs/policy_download_list.md`)
- **Clear saved sessions** button in the sidebar with a confirmation step (`app.py`)
- **Collapsible result panels** — Analysis and Agent Activity Log are now stacked vertically and can be folded/unfolded (`app.py`)

### Changed

- **Demo questions** — replaced the original 6 preset questions with 4 stakeholder-aligned questions (South Africa vs Kenya, health data SA vs Nigeria, multi-country gap analysis, national laws vs AU Malabo). Uganda references replaced with Nigeria because the Uganda PDF is not available (`config.py`, `app.py`)
- **Knowledge base size** — expanded from 7 documents / 583 chunks to 17 documents / 1,450 chunks (`config.py`, `README.md`)
- **Sidebar stack info** — updated to reflect vLLM on ACE HPC A100 instead of local Ollama (`app.py`, `README.md`)
- **README refresh** — badges, tech stack, setup instructions, hardware notes, project structure, and limitations updated to match the vLLM/A100 setup and two-tab UI (`README.md`)

### Fixed

- **White text on white background** in the About tab and analysis card — added explicit `color: #1e293b` to `.answer-card` and `.about-card` CSS rules (`app.py`)
- **Broken emoji rendering** in sidebar country list and log search indicator (`app.py`)
- **Sidebar policy/governance section** — added the new AU strategy documents to the sidebar knowledge base list (`app.py`)

---

## [0.1.2] — 2026-06-15

### Fixed

- **Analysis panel blank** — `main_answer` was injected raw into an HTML `<div>` via `unsafe_allow_html=True`; Streamlit renders each `st.markdown()` call as an independent DOM node, so a split open/close `<div>` pair never wraps the content. Fixed by converting the LLM's markdown to HTML using the `markdown` library and injecting the full card as a single atomic `st.markdown()` call (`app.py`)
- **`config.py` IndentationError** — a stray leading space before the module docstring (`  """`) caused Python to raise `IndentationError: unexpected indent` on startup, crashing the entire app on import; removed the leading whitespace (`config.py`)

### Added

- **Session history persistence** — every completed query is now auto-saved to `sessions/<timestamp>_<slug>.json` (question, final answer, process log, sub-questions). A "Past Sessions" section in the sidebar lists the 10 most recent sessions, each expandable to read the full answer and download it as `.txt` (`app.py`)
- `sessions/` directory created automatically on startup via `os.makedirs(..., exist_ok=True)`

### Changed

- **Relevance score threshold filter** (`retrieval.py`) — chunks with a similarity score below `0.45` are now discarded in `format_context()` before being passed to the synthesizer. Previously low-confidence chunks (e.g. score 0.3) were passed as authoritative context, causing the LLM to either waste context window or hallucinate section connections. When all chunks for a sub-question fall below threshold, the synthesizer receives an explicit "no sufficiently relevant passages" message instead of silence
- **Passage grounding in synthesizer** (`nodes.py`, `prompts/synthesizer.txt`) — context sent to the synthesizer is now structured into labelled `BLOCK N: COUNTRY` sections with globally renumbered passages and declared passage ranges per block. Blocks with no usable evidence carry an explicit `"Do NOT fabricate provisions"` instruction. The synthesizer prompt updated with a matching rule: cite only from the block's declared passages; if a block says do not fabricate, state that information was unavailable for that country
- `markdown` package (already in venv) imported in `app.py` to power the `md.markdown()` HTML conversion with `nl2br` and `tables` extensions

---

## [0.1.1] — 2026-06-15

### Added
- `docs/eswatini.pdf` — Data Protection Act, 2022 (Eswatini) · 32 pages · 60 chunks
- `docs/zimbabwe1.pdf` — Data Protection Act [Chapter 11:12], 2021 (Zimbabwe) · 37 pages · 81 chunks
- Eswatini and Zimbabwe registered in `config.py` DOCUMENTS registry
- `prompts/planner.txt` updated: Eswatini and Zimbabwe added to available countries list

### Changed
- Total knowledge base: 442 → 583 chunks across 7 jurisdictions (6 countries + AU)
- `.gitignore` updated: PDFs are now committed directly (all <1 MB, text-based, total ~4.4 MB)
- `.gitattributes` updated: PDF files marked as binary to prevent line-ending conversion
- README knowledge base table updated to reflect 7 documents and 583 chunks
- A100 migration guide added to README (model comparison, Linux setup, config changes, benchmarking tips)

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

[Unreleased]: https://github.com/atwine/Africa-Policy-Lens/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/atwine/Africa-Policy-Lens/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/atwine/Africa-Policy-Lens/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/atwine/Africa-Policy-Lens/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/atwine/Africa-Policy-Lens/releases/tag/v0.0.1
