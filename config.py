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
    "What conditions and safeguards are required for sharing health data across South Africa, Nigeria, and Botswana?",
    "What legal mechanisms currently support, and what gaps hinder, sharing public health data across South Africa, Kenya, and Nigeria?",
    "What are the common themes between data governance at the national level versus the AU Malabo Convention, and where are there divergences?"
]
