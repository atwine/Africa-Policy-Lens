# PolicyLens — Presentation Brief for NotebookLM (v2)
*ABI AI Community of Practice · July 2, 2026*
*Author: Mugume Twinamatsiko Atwine, ML Engineer / Data Scientist, ACE, IDI Kampala*

> **Note on this document:** Each section is labelled `[Plain language]` or `[Technical detail]` so that NotebookLM can treat them as distinct knowledge layers. Plain-language sections are the primary content for slides. Technical-detail sections are supporting evidence for deeper questions.

---

## Slide 1 — What Is PolicyLens and Why Does It Exist?

> [Plain language]

**Core claim:** PolicyLens is the first open-source, African-built AI research assistant that can compare data protection laws across multiple African countries simultaneously, citing the exact clause it draws from, without relying on any commercial cloud service.

PolicyLens is an AI-powered policy analysis tool purpose-built for African data protection law. It was developed to support researchers, legal analysts, and policy professionals who need to reason across multiple African countries' data protection frameworks simultaneously — a task that conventional search and standard AI assistants handle poorly.

### The core problem it solves

When a researcher asks "What are the cross-border data transfer rules under South Africa's POPIA versus Kenya's Data Protection Act, and how do they align with the AU Malabo Convention?", a standard AI assistant will fail in three predictable ways:

- **Terminology mismatch.** The user says "data sharing"; the law says "transborder flow of personal information." A keyword search returns nothing useful.
- **Multi-jurisdiction collapse.** A single search across all documents returns a jumbled mix of passages from different countries with no country-level structure.
- **Hallucination risk.** When the retrieved context is thin, the model fills gaps by inventing section numbers or legal provisions that do not exist.

PolicyLens solves all three by decomposing the question, searching each jurisdiction separately, verifying that the evidence is sufficient, rewriting the query if it is not, and only then writing a formally cited answer.

### Who it is for

- Research consortia coordinating data sharing studies across African countries
- Legal and compliance teams advising on cross-border data flows
- Policy analysts comparing national laws against continental frameworks
- Community of Practice members exploring AI-assisted legal research

### Demo context

This MVP was built for the **ABI AI Community of Practice Meeting on July 2, 2026** and runs entirely on local and institutional infrastructure — no commercial cloud API keys are required.

### Visual Representation

> [Plain language]

**Metaphor — The Overwhelmed Research Assistant**

Imagine you ask a new intern to compare data-sharing rules across six African countries. If they have never worked with legal documents before, they will do one of three things: search the wrong words and find nothing, pull random pages from the wrong country, or — worst of all — make up an answer that sounds plausible but is wrong. That is exactly what a standard AI assistant does. PolicyLens is the experienced senior researcher who first reads the full shelf of law books, tags every paragraph by country, and only speaks when they have the right passage in hand.

```
WITHOUT PolicyLens                   WITH PolicyLens
─────────────────────────────────    ──────────────────────────────────
You ask one question                 You ask one question
        │                                    │
        ▼                                    ▼
AI searches everything at once       AI breaks it into focused
        │                            sub-questions per country
        ▼                                    │
Returns a jumbled mix of             Searches each country's
pages from random countries          documents separately
        │                                    │
        ▼                                    ▼
Possibly invents missing details     Checks if evidence is good enough
                                             │
                                             ▼
                                     Writes a cited, country-by-country
                                     answer with section numbers
```

**What the diagram above means in plain words:** Without PolicyLens, one broad search dumps a mixed pile of results from all countries and the AI may invent what it cannot find. With PolicyLens, the same question is split into focused sub-questions — one per country — each country's documents are searched separately, the evidence is checked for quality before being used, and the final answer traces every claim back to a specific section number in the source law. The difference is not speed; it is reliability and traceability.

**One-sentence version for any audience:** PolicyLens is a legal research assistant that reads African data protection laws so you do not have to, and it always shows you exactly which clause it is quoting.

---

## Slide 2 — The Four-Stage Agentic Pipeline

> [Plain language]

**Core claim:** PolicyLens processes every question through four specialist stages in sequence — plan, retrieve-and-verify, synthesise, and suggest follow-ups — because no single AI prompt can reliably do all four jobs at once without introducing errors or omissions.

PolicyLens does not issue a single search query and return whatever comes back. Every question travels through four distinct stages, each with a single, well-defined job.

### Stage 1 — Planner

The AI's first job is not to answer — it is to think strategically. Given the user's question, which countries or policy scopes does it touch, and what is the sharpest sub-question to ask per scope?

For example, a question about South Africa and Kenya on data sharing for research produces five sub-questions:
1. Cross-border transfer conditions under South African law
2. Cross-border transfer conditions under Kenyan law
3. The AU Malabo Convention's treatment of cross-border research data flows
4. Data subject rights in South African research data sharing
5. Data subject rights in Kenyan research data sharing

Each sub-question is tagged with a target country or scope. This list is the research plan that drives everything that follows.

### Stage 2 — Retriever, Evaluator, and Rewriter (the retrieval loop)

> [Technical detail]

For each sub-question, the pipeline runs a retrieval loop:

**Retriever:** The vector database is searched using the sub-question text as the query. The search is filtered by the target country or scope, so passages from unrelated jurisdictions are never returned. The top-5 most semantically similar chunks are retrieved.

**Evaluator:** The retrieved passages are sent to the AI with a single question: "Is this context sufficient to answer the sub-question?" The model returns either SUFFICIENT or INSUFFICIENT.

**Rewriter:** If the verdict is INSUFFICIENT, the query is rewritten using alternative legal terminology — for example, swapping "data sharing" for "transborder flow of personal information". The retrieval is then retried. This loop runs up to two times per sub-question before the pipeline accepts whatever is available and moves on.

This loop ensures that the answer writer only receives verified, high-quality evidence per jurisdiction.

### Stage 3 — Synthesiser

Once all sub-questions have been processed, the AI writes the final answer. It is instructed to cite specific section numbers, structure the answer by jurisdiction for comparison questions, and explicitly flag any jurisdiction where evidence was insufficient rather than inventing provisions.

### Stage 4 — Follow-up Generator

After the answer is produced, the AI generates 3–5 grounded follow-up questions derived from what was actually found in the documents. These appear as clickable buttons in the interface so the user can immediately drill deeper.

### Visual Representation

> [Plain language]

**Metaphor — A Team of Four Specialists, Not One Generalist**

Think of PolicyLens as a small team working in relay, where each member has exactly one job and passes the baton to the next:

```
YOUR QUESTION
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│  RUNNER 1 — The Strategist (Planner)                            │
│  "What exactly needs to be looked up, and in which country?"    │
│  Output: a numbered list of focused sub-questions per country   │
└─────────────────────┬───────────────────────────────────────────┘
                      │  hands off the research plan
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  RUNNER 2 — The Librarian (Retriever + Evaluator + Rewriter)    │
│                                                                 │
│  For EACH sub-question:                                         │
│   1. Pull the most relevant pages from that country's law       │
│   2. Ask: "Is this enough to answer the question?"              │
│      ├── YES → pass the pages forward                           │
│      └── NO  → rephrase the search using legal synonyms         │
│                and try again (up to 2 retries)                  │
└─────────────────────┬───────────────────────────────────────────┘
                      │  hands off verified evidence
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  RUNNER 3 — The Writer (Synthesiser)                            │
│  "Write a formal answer, citing the exact clause numbers."      │
│  Output: a structured answer, e.g. "South Africa: Section 72   │
│  of POPIA [Passage 3] states... Kenya: Section 48 [Passage 7]  │
│  states..."                                                     │
└─────────────────────┬───────────────────────────────────────────┘
                      │  hands off the completed answer
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  RUNNER 4 — The Curator (Follow-up Generator)                   │
│  "Based on what we actually found, what should you ask next?"   │
│  Output: 3–5 clickable follow-up questions in the UI            │
└─────────────────────────────────────────────────────────────────┘
```

**What the diagram above means in plain words:** The Strategist decides what to look for. The Librarian finds it, double-checks it, and rephrases the search if the first attempt comes up short. The Writer turns the verified evidence into a formally cited answer. The Curator uses that same evidence to suggest the next useful questions. No single stage can be skipped — if the Librarian sends weak evidence, the Writer's answer is weak; if there is no Strategist, the Librarian searches the wrong things.

**Why four stages instead of one?** Because combining all of these into one prompt produces answers that are vague, uncited, and unable to say "I don't have enough evidence for this country." The relay structure makes each step auditable and replaceable independently.

---

## Slide 3 — System Architecture and Component Connectivity

> [Plain language]

**Core claim:** PolicyLens runs entirely on African institutional infrastructure — an A100 GPU at the African Centre of Excellence High Performance Computing facility in Kampala and a standard laptop — with zero dependency on commercial cloud services such as OpenAI, Google, or AWS.

PolicyLens is split into three layers: the **interface layer** (what you see), the **compute layer** (where the thinking happens), and the **data layer** (where the documents live). Each layer uses a separate technology, and they communicate in a fixed sequence every time a question is asked.

### Compute Layer — Two separate inference endpoints

> [Technical detail]

**LLM reasoning — ACE HPC A100 80GB via vLLM**
The four planning, evaluation, rewriting, and synthesis calls all go to a remote server running **vLLM** on an NVIDIA A100 80GB GPU hosted at the African Centre of Excellence High Performance Computing facility in Kampala. The model is **Llama 3.3 70B Instruct AWQ INT4**, a quantised version of Meta's flagship open-source instruction-following model. vLLM exposes an OpenAI-compatible REST API so the application connects to it without modification. No commercial API keys are required.

**Embeddings — Ollama running locally**
Turning text into vector representations is done by **nomic-embed-text**, a compact open-source embedding model served by **Ollama** on the local machine. Embeddings are only needed at ingestion time and at query time. Keeping this local avoids latency to a remote server for every search call.

### Data Layer — ChromaDB vector store

> [Technical detail]

All 17 source documents (1,450 chunks total) are stored in a **ChromaDB** persistent collection on local disk. Each chunk carries seven metadata fields: `country`, `document_name`, `document_type`, `section_heading`, `start_page`, `end_page`, and `chunk_index`. The country metadata field is what makes jurisdiction-filtered search possible — every query is restricted to only the chunks from the target country or scope, so passages from unrelated jurisdictions are never returned.

Ingestion is a one-time step: each PDF is read and split into 1,500-character overlapping chunks, an embedding is generated for each chunk, and everything is written to ChromaDB with the associated metadata.

### Interface Layer — Streamlit web application

> [Plain language]

The user-facing application runs in a browser on the analyst's laptop. It has two tabs:

**About tab:** Project overview, knowledge base table showing all 17 documents, sample questions, and tech stack.

**PolicyLens tab:** Four preset demo question buttons, a free-text input box, and the live analysis interface. When a question is submitted, a streaming status widget updates in real time — the user sees each stage complete as it happens. When the pipeline finishes, the answer appears with a Sources panel listing every retrieved passage and its relevance score, a copy-to-clipboard button, and a Markdown download button.

### Orchestration — LangGraph

> [Technical detail]

The four stages are wired together by **LangGraph's StateGraph**, which defines nodes (the agent functions), edges (the fixed sequence of calls), and conditional edges (the retry-or-advance decision after evaluation). The full state — question, plan, sub-questions, retrieved chunks, passage records, log, and final answer — flows through a typed Python dictionary that each node reads from and writes to. `graph.stream()` is used at query time so the UI can receive stage-by-stage updates rather than waiting for the entire pipeline to finish.

### Visual Representation

> [Plain language]

**Metaphor — A Kitchen, a Pantry, and a Pass-Through Window**

The three layers work exactly like a restaurant:

```
┌──────────────────────────────────────────────────────────────────────┐
│  THE DINING ROOM  (Interface Layer — what you see)                   │
│                                                                      │
│  You sit at a table (the browser), read the menu (preset questions), │
│  and place your order (type your question). A live ticket screen     │
│  above the kitchen pass-through shows you exactly what the kitchen   │
│  is working on in real time.                                         │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Streamlit web app running on your laptop                      │  │
│  │  • Question input box       • Live status ticker               │  │
│  │  • Preset question buttons  • Answer card with citations       │  │
│  │  • Follow-up buttons        • Copy + Download buttons          │  │
│  └────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬──────────────────────────────────────┘
                                │  your question travels down
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│  THE KITCHEN  (Compute Layer — where the thinking happens)           │
│                                                                      │
│  Two chefs, two specialties:                                         │
│                                                                      │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐  │
│  │  HEAD CHEF — ACE HPC A100    │  │  SOUS CHEF — Laptop (Ollama) │  │
│  │  (the big GPU in Kampala)    │  │  (runs locally)              │  │
│  │                              │  │                              │  │
│  │  Handles all the reasoning:  │  │  Handles one job only:       │  │
│  │  planning, evaluating,       │  │  turning text into numbers   │  │
│  │  rewriting, synthesising.    │  │  (embeddings) so the pantry  │  │
│  │                              │  │  can be searched by meaning, │  │
│  │  Model: Llama 3.3 70B        │  │  not just by keyword.        │  │
│  │  (70 billion parameters,     │  │                              │  │
│  │  fits on one 80GB GPU card)  │  │  Model: nomic-embed-text     │  │
│  │                              │  │  (274 MB, runs on CPU)       │  │
│  └──────────────────────────────┘  └──────────────────────────────┘  │
└───────────────────────────────┬──────────────────────────────────────┘
                                │  searches and results
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│  THE PANTRY  (Data Layer — where the documents live)                 │
│                                                                      │
│  17 policy documents, pre-sliced into 1,450 labelled paragraphs.    │
│  Every paragraph is tagged: which country, which document, which     │
│  page. When the kitchen asks for "Kenya, data transfers", only       │
│  Kenya's paragraphs are pulled — nothing from South Africa leaks in. │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  ChromaDB vector store (on disk, local)                        │  │
│  │  Labels on every paragraph: country · document · page · section│  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

**What the diagram above means in plain words:** The Dining Room is the browser interface on your laptop — where you type your question and read the answer. The Kitchen is where the AI model runs: a powerful GPU server in Kampala handles all the complex reasoning, while a small local model on your own machine handles the simpler task of converting text into searchable numbers. The Pantry is the document store on your hard drive, where all 17 policy documents have been pre-labelled so the right country's paragraphs can be pulled instantly without mixing up jurisdictions.

**Key insight for a non-technical audience:** Nothing in this stack costs money to run. The GPU is institutional (ACE HPC), the AI models are open-source and free to download, and the database runs on your own hard drive. There is no subscription to OpenAI, Google, or any commercial service.

---

## Slide 4 — Knowledge Base, Results, and What Comes Next

> [Plain language]

**Core claim:** PolicyLens already holds 1,450 labelled paragraphs from 17 African and international policy documents, produces a fully cited multi-jurisdiction answer in under 90 seconds, and has a clear two-track roadmap — broader geographic coverage and faster response time — that can both be delivered within six months.

### What is in the knowledge base

The document store contains **1,450 text paragraphs** extracted from **17 documents** across **13 jurisdictions or policy scopes**:

**Binding national and continental laws (583 paragraphs):**
South Africa — Protection of Personal Information Act (POPIA), 2013 · Kenya — Data Protection Act, 2019 · Nigeria — Nigeria Data Protection Act, 2023 · Botswana — Data Protection Act, 2018 · Eswatini — Data Protection Act, 2022 · Zimbabwe — Data Protection Act, 2021 · African Union — Malabo Convention on Cyber Security and Personal Data Protection, 2014

**Policy and governance documents (867 paragraphs):**
AU Digital Transformation Strategy for Africa (2020–2030) · AU Continental AI Strategy (2024) · AU Science, Technology and Innovation Strategy STISA 2034 · AU Data Policy Framework (2022) · EU-Africa PerMed Policy Brief on Personalised Medicine Collaboration (2025) · OECD guidance on secondary use of health data across borders (2025) · Pathogen Data Network Data Publishing Policy (2025) · SADC Cyber-Infrastructure Framework (2016) · Wellcome Trust report on pathogen genomic sequence data sharing (2025) · Thaldar et al. on communicating clearly about data sharing in genomics (Human Genomics, 2025)

### What a real query looks like

A question such as "Where do South Africa and Kenya align versus conflict on data sharing for research?" produces a five-sub-question research plan. The pipeline runs 5–10 searches across the document store (with retries if context is insufficient), retrieves up to 50 individual passages, and synthesises a structured answer of approximately 2,000–4,000 characters in 30–90 seconds. The answer cites specific section numbers — for example, "Section 72(1)(a) of South Africa's POPIA [Passage 3]" — and ends with 3–5 follow-up questions the user can click to continue the analysis.

### The compute split in practice

> [Technical detail]

The A100 GPU on ACE HPC handles the 70B parameter model. A 70B model at INT4 quantisation occupies approximately 35GB of GPU memory, which fits on a single A100 80GB card. Each AI call (plan, evaluate, rewrite, synthesise) takes 5–20 seconds depending on context length. The total pipeline time of 30–90 seconds is dominated by the 4–6 sequential AI calls; the document searches and embedding calls complete in under a second each. The local embedding model (approximately 274MB) runs on CPU and must be running on the same machine as the web application.

### What this demonstrates for the Community of Practice

> [Plain language]

PolicyLens is a working proof-of-concept that **open-source models running on African institutional compute** can produce legally grounded, multi-jurisdiction policy analysis — without any commercial cloud dependency. The entire stack is open source. The model weights are publicly available. The document store, embedding model, and orchestration framework are all free. The only infrastructure required is one GPU server and a laptop.

### Immediate next steps

> [Plain language]

The next phase has two independent tracks that can run in parallel: **coverage** (adding more countries' laws) and **performance** (making queries faster). Neither depends on the other, so both can be delivered simultaneously over the next three to six months.

**Coverage track:**
- Add Rwanda, Tanzania, and Ghana data protection laws to the knowledge base
- Side-by-side clause comparison view in the interface

**Performance track:**
- Parallel sub-question retrieval to reduce total pipeline time from ~60s to ~20s
- Conversation threading so follow-up answers accumulate in a single downloadable document

**Access track:**
- Hugging Face Spaces deployment so Community of Practice members can use PolicyLens from a browser without any local setup

### Visual Representation

> [Plain language]

**Metaphor — A Filled Bookshelf, a Stopwatch, and a Promise**

```
THE BOOKSHELF TODAY
───────────────────────────────────────────────────────────────────

  LAWS (the rules that must be followed)        POLICY DOCS (the plans & frameworks)
  ┌───────┐ ┌───────┐ ┌───────┐ ┌─────┐        ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
  │  🇿🇦   │ │  🇰🇪   │ │  🇳🇬   │ │ AU  │        │ AU  │ │ AU  │ │OECD │ │Wells│
  │ POPIA │ │ DPA   │ │ NDPA  │ │Mala-│        │DTS  │ │ AI  │ │Hlth │ │come │
  │ 2013  │ │ 2019  │ │ 2023  │ │ bo  │        │2030 │ │Strat│ │Data │ │ Path│
  └───────┘ └───────┘ └───────┘ └─────┘        └─────┘ └─────┘ └─────┘ └─────┘
  ┌───────┐ ┌───────┐ ┌───────┐                ┌─────┐ ┌─────┐ ┌─────┐
  │  🇧🇼   │ │  🇸🇿   │ │  🇿🇼   │                │SADC │ │ AU  │ │Path.│
  │ DPA   │ │ DPA   │ │ DPA   │                │Cyber│ │Data │ │Data │
  │ 2018  │ │ 2022  │ │ 2021  │                │Frmwk│ │Polcy│ │Netw.│
  └───────┘ └───────┘ └───────┘                └─────┘ └─────┘ └─────┘

  Total: 17 documents · 1,450 labelled paragraphs · 13 jurisdictions / scopes


WHAT HAPPENS WHEN YOU ASK A QUESTION
───────────────────────────────────────────────────────────────────

  You type your question                                       0 s
        │
        ▼
  AI builds a research plan (Planner)                    ~5–10 s
        │
        ▼
  AI reads the right shelves, checks the evidence,       ~15–60 s
  re-reads if needed (Retriever / Evaluator / Rewriter)
        │
        ▼
  AI writes a cited, country-by-country answer           ~10–20 s
  (Synthesiser)
        │
        ▼
  AI suggests your next questions (Follow-up Generator)   ~5–10 s
        │
        ▼
  You read a fully cited answer on screen               30–90 s total


WHAT COMES NEXT — THE ROADMAP
───────────────────────────────────────────────────────────────────

  NOW (MVP, live today)
  ├── 7 national laws + 10 policy frameworks
  ├── Single-user, runs on one laptop + ACE HPC
  └── Answer in ~60 seconds

  NEXT (3–6 months)
  ├── + Rwanda, Tanzania, Ghana laws  →  10 national laws
  ├── Parallel retrieval              →  answer in ~20 seconds
  ├── Side-by-side clause comparison view
  └── Hugging Face Spaces             →  accessible by browser, no setup

  VISION
  └── A shared African policy intelligence layer that any researcher,
      regulator, or community member can query in plain language —
      built on African compute, using African institutional knowledge.
```

**What the diagram above means in plain words:** The bookshelf shows every document PolicyLens can already read and reason from — seven national laws and ten continental or international policy frameworks. The stopwatch shows that a complete, cited answer takes less than 90 seconds from the moment you press Enter. The roadmap shows two things happening in parallel over the next six months: the bookshelf grows (more countries) and the stopwatch shrinks (faster responses), while a web deployment makes the tool available to anyone in the Community of Practice without needing to install anything.

**The big-picture message:** PolicyLens proves that African research institutions do not need to rent intelligence from Silicon Valley. The GPU is in Kampala. The law books are African. The answer cites the clause. This is what sovereign AI-assisted research looks like.

---

## Conclusion

> [Plain language]

PolicyLens demonstrates three things that matter for the ABI Community of Practice.

First, **it works.** A single plain-language question produces a formally cited, multi-jurisdiction policy analysis in under 90 seconds, drawing only from real document passages and refusing to invent what it cannot find.

Second, **it is ours.** Every component — the AI model, the document store, the orchestration framework, the interface — is open-source. The GPU is at ACE HPC in Kampala. There is no commercial dependency and no data leaving African institutional infrastructure.

Third, **it is a starting point, not a finished product.** The knowledge base can be extended to any African country whose laws are available as text. The pipeline architecture scales to any policy domain. The interface can be deployed as a shared web tool accessible to anyone in the network. What exists today is a proof that the approach is sound — the next step is to build it out together.
