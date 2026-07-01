"""
config.py
---------
Central configuration for PolicyLens.
All constants in one place — change settings here, not in individual files.
"""

# ---------------------------------------------------------------------------
# LLM settings — vLLM endpoint (Llama 3.3 70B Instruct AWQ INT4 on A100)
# ---------------------------------------------------------------------------
VLLM_BASE_URL = "http://10.35.50.41:8000/v1"      # OpenAI-compatible vLLM endpoint
LLM_MODEL = "ibnzterrell/Meta-Llama-3.3-70B-Instruct-AWQ-INT4"
LLM_TEMPERATURE = 0.1  # Low temperature for precise, deterministic legal analysis

# ---------------------------------------------------------------------------
# Ollama settings — used for embeddings only (nomic-embed-text stays local)
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL = "http://localhost:11434"
EMBEDDING_MODEL = "nomic-embed-text"

# ---------------------------------------------------------------------------
# ChromaDB settings
# ---------------------------------------------------------------------------
CHROMA_PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "policy_documents"

# ---------------------------------------------------------------------------
# Additional documents directory
# Policy/governance PDFs added July 2026 live here, separate from the original
# binding-law PDFs in docs/.
# ---------------------------------------------------------------------------
NEW_DOCS_DIR = "docs/policy_governance"

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
    "Nigeria_Data_Protection_Act_2023.pdf": {
        "country": "Nigeria",
        "document_type": "binding_law",
        "document_name": "Nigeria Data Protection Act, 2023"
    },
    "botswana.pdf": {
        "country": "Botswana",
        "document_type": "binding_law",
        "document_name": "Data Protection Act, 2018 (Botswana)"
    },
    "eswatini.pdf": {
        "country": "Eswatini",
        "document_type": "binding_law",
        "document_name": "Data Protection Act, 2022 (Eswatini)"
    },
    "zimbabwe1.pdf": {
        "country": "Zimbabwe",
        "document_type": "binding_law",
        "document_name": "Data Protection Act [Chapter 11:12], 2021 (Zimbabwe)"
    },
    "au_malabo_convention.pdf": {
        "country": "African Union",
        "document_type": "binding_law",
        "document_name": "AU Convention on Cyber Security and Personal Data Protection (Malabo Convention), 2014"
    },

    # ── Policy & governance documents (added July 2026) ────────────────────
    "38507-doc-dts-english.pdf": {
        "country": "African Union",
        "document_type": "continental_strategy",
        "document_name": "AU Digital Transformation Strategy for Africa (2020-2030)",
        "source_dir": "docs/policy_governance"
    },
    "44004-doc-EN-_Continental_AI_Strategy_July_2024.pdf": {
        "country": "African Union",
        "document_type": "continental_strategy",
        "document_name": "Continental Artificial Intelligence Strategy, July 2024",
        "source_dir": "docs/policy_governance"
    },
    "45087-doc-AU_STISA_2025-2034_Strategy_ENGLISH.pdf": {
        "country": "African Union",
        "document_type": "continental_strategy",
        "document_name": "AU Science, Technology and Innovation Strategy (STISA 2024), 2025-2034",
        "source_dir": "docs/policy_governance"
    },
    "AU-DATA-POLICY-FRAMEWORK-2024-ENG-V2.pdf": {
        "country": "African Union",
        "document_type": "continental_policy",
        "document_name": "AU Data Policy Framework, 2022",
        "source_dir": "docs/policy_governance"
    },
    "EU-Africa Permed Policy brief nº2.pdf": {
        "country": "EU-Africa",
        "document_type": "policy_brief",
        "document_name": "EU-Africa PerMed Policy Brief No. 2 — Personalised Medicine Collaboration, January 2025",
        "source_dir": "docs/policy_governance"
    },
    "OECD secondary use of data.pdf": {
        "country": "OECD",
        "document_type": "international_guideline",
        "document_name": "OECD — Facilitating the Secondary Use of Health Data for Public Interest Purposes Across Borders, June 2025",
        "source_dir": "docs/policy_governance"
    },
    "PDN Data Publishing Policy V2.pdf": {
        "country": "Pathogen Data Network",
        "document_type": "institutional_policy",
        "document_name": "Pathogen Data Network (PDN) Data Publishing Policy Version 2, June 2025",
        "source_dir": "docs/policy_governance"
    },
    "s40246-025-00784-z.pdf": {
        "country": "International",
        "document_type": "journal_article",
        "document_name": "Thaldar et al. — Communicating clearly about data sharing in genomics (Human Genomics, 2025)",
        "source_dir": "docs/policy_governance"
    },
    "SADC CI Framework 20160622.final 24 June 2016 11 .pdf": {
        "country": "SADC",
        "document_type": "regional_framework",
        "document_name": "SADC Cyber-Infrastructure Framework, June 2016",
        "source_dir": "docs/policy_governance"
    },
    "Wellcome Report_Tackling PGS Data Sharing Challenges 2025.pdf": {
        "country": "Wellcome Trust",
        "document_type": "research_report",
        "document_name": "Wellcome Report — Tackling Pathogen Genomic Sequence Data Sharing Challenges in Low-Resource Settings, 2025",
        "source_dir": "docs/policy_governance"
    }
}

# ---------------------------------------------------------------------------
# Demo preset questions (displayed as buttons in Streamlit UI)
# ---------------------------------------------------------------------------
DEMO_QUESTIONS = [
    "Where do the data protection laws of South Africa and Kenya align versus conflict with each other on data sharing for research?",
    "What conditions and safeguards are required for sharing health data between South Africa and Nigeria?",
    "What legal mechanisms currently support, and what gaps hinder, sharing public health data across South Africa, Kenya, and Nigeria?",
    "What are the common themes between data governance at the national level versus the AU Malabo Convention, and where are there divergences?"
]
