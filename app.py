"""
app.py
------
PolicyLens — Streamlit Frontend.

Provides:
- Two-tab layout: About + PolicyLens
- About tab: project overview, knowledge base, sample questions, how it works
- PolicyLens tab: preset demo questions, free-text input, agent log, cited analysis

Usage:
    streamlit run app.py
"""

import json
import os
from datetime import datetime
import markdown as md  # converts LLM markdown text -> HTML for safe injection
import streamlit as st
from graph import run_query
from config import DEMO_QUESTIONS, DOCUMENTS

# Directory where completed sessions are persisted
SESSIONS_DIR = os.path.join(os.path.dirname(__file__), "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)


def save_session(question: str, result: dict) -> str:
    """Saves a completed query result to a timestamped JSON file. Returns the file path."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Sanitise question to a short slug for the filename
    slug = "".join(c if c.isalnum() or c in " _-" else "" for c in question[:40]).strip().replace(" ", "_")
    filename = f"{ts}_{slug}.json"
    filepath = os.path.join(SESSIONS_DIR, filename)
    payload = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "final_answer": result.get("final_answer", ""),
        "process_log": result.get("process_log", []),
        "sub_questions": result.get("sub_questions", []),
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return filepath


def load_sessions() -> list[dict]:
    """Returns all saved sessions sorted newest-first."""
    sessions = []
    for fname in sorted(os.listdir(SESSIONS_DIR), reverse=True):
        if fname.endswith(".json"):
            try:
                with open(os.path.join(SESSIONS_DIR, fname), "r", encoding="utf-8") as f:
                    sessions.append(json.load(f))
            except Exception:
                pass  # Skip unreadable files
    return sessions


# ---------------------------------------------------------------------------
# Page configuration — must be first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="PolicyLens — African Data Protection",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* Global font & background */
html, body, [class*="css"] {
    font-family: 'Segoe UI', sans-serif;
}

/* Hero header */
.hero {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 12px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    color: white;
}
.hero h1 { font-size: 2.4rem; margin: 0 0 0.3rem 0; font-weight: 700; }
.hero p  { font-size: 1.05rem; margin: 0; opacity: 0.85; }

/* Section headers */
.section-header {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #6b7280;
    margin: 1.5rem 0 0.6rem 0;
}

/* Preset question buttons */
div.stButton > button {
    background: #ffffff;
    border: 1.5px solid #e2e8f0;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    text-align: left;
    font-size: 0.88rem;
    color: #1e293b;
    line-height: 1.4;
    transition: all 0.15s ease;
    white-space: normal;
    height: auto;
}
div.stButton > button:hover {
    border-color: #3b82f6;
    background: #eff6ff;
    color: #1d4ed8;
    box-shadow: 0 2px 8px rgba(59,130,246,0.15);
}

/* Ask button (primary) */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1d4ed8, #3b82f6);
    color: white;
    border: none;
    font-weight: 600;
    font-size: 0.95rem;
}
div.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #1e40af, #2563eb);
    color: white;
    box-shadow: 0 4px 12px rgba(59,130,246,0.4);
}

/* Active question banner */
.question-banner {
    background: #eff6ff;
    border-left: 4px solid #3b82f6;
    border-radius: 0 8px 8px 0;
    padding: 0.9rem 1.2rem;
    margin: 1rem 0;
    color: #1e3a5f;
    font-size: 1rem;
    font-style: italic;
}

/* Process log box */
.log-box {
    background: #0f172a;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 0.83rem;
    color: #94a3b8;
    line-height: 1.7;
    margin-bottom: 1rem;
}
.log-stage  { color: #38bdf8; font-weight: 700; }
.log-ok     { color: #4ade80; }
.log-warn   { color: #facc15; }
.log-search { color: #c084fc; }
.log-rewrite{ color: #fb923c; }
.log-synth  { color: #f472b6; }

/* Answer card */
.answer-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.8rem 2rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    margin-top: 0.5rem;
    color: #1e293b;
}
.answer-card h1, .answer-card h2, .answer-card h3, .answer-card h4 {
    color: #0f172a;
}
.answer-card p, .answer-card li, .answer-card td, .answer-card th {
    color: #1e293b;
}
.answer-card code {
    color: #0f172a;
    background: #f1f5f9;
}

/* About tab cards */
.about-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.5rem 1.8rem;
    box-shadow: 0 1px 6px rgba(0,0,0,0.04);
    margin-bottom: 1rem;
}
.about-card h3 {
    margin-top: 0;
    color: #0f172a;
}
.about-card {
    color: #1e293b;
}
.about-card p, .about-card li {
    color: #1e293b;
}

/* Sidebar styling */
.sidebar-badge {
    display: inline-block;
    background: #dbeafe;
    color: #1e40af;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
    margin: 0.15rem 0.1rem;
}
.sidebar-section {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #9ca3af;
    margin: 1rem 0 0.4rem 0;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚖️ PolicyLens")
    st.markdown("*African Data Protection Policy Assistant*")
    st.markdown("---")

    st.markdown('<div class="sidebar-section">Knowledge Base</div>', unsafe_allow_html=True)
    countries = {
        "🇿🇦 South Africa": "POPIA, 2013",
        "🇰🇪 Kenya": "Data Protection Act, 2019",
        "🇳🇬 Nigeria": "NDPA, 2023",
        "🇧🇼 Botswana": "Data Protection Act, 2018",
        "🇸🇿 Eswatini": "Data Protection Act, 2022",
        "🇿🇼 Zimbabwe": "Data Protection Act, 2021",
        "🌍 African Union": "Malabo Convention, 2014",
    }
    policy_docs = {
        "📘 AU Digital Transformation Strategy": "2020-2030",
        "🤖 AU Continental AI Strategy": "July 2024",
        "🔬 AU STISA 2034": "2025-2034",
        "📊 AU Data Policy Framework": "2022",
        "🇪🇺🇿🇦 EU-Africa PerMed": "Policy Brief, 2025",
        "🌐 OECD Health Data Secondary Use": "June 2025",
        "🧬 Pathogen Data Network Publishing Policy": "Version 2, 2025",
        "📄 SADC Cyber-Infrastructure Framework": "2016",
        "🔬 Wellcome PGS Data Sharing Report": "2025",
        "🧬 Thaldar et al. — Genomics Data Sharing": "Human Genomics, 2025",
    }
    for flag_country, law in countries.items():
        st.markdown(f"**{flag_country}**  \n*{law}*")
    st.markdown("<div class='sidebar-section'>Policy & Governance</div>", unsafe_allow_html=True)
    for doc, year in policy_docs.items():
        st.markdown(f"**{doc}**  \n*{year}*")

    st.markdown("---")
    st.markdown('<div class="sidebar-section">Pipeline</div>', unsafe_allow_html=True)
    st.markdown("""
1. **Planner** — breaks question into sub-queries per country
2. **Retriever** — searches ChromaDB with metadata filtering
3. **Evaluator** — checks if context is sufficient
4. **Rewriter** — rewrites query using legal synonyms (if needed)
5. **Synthesizer** — generates a formal cited answer
""")

    st.markdown("---")
    st.markdown('<div class="sidebar-section">Stack</div>', unsafe_allow_html=True)
    st.markdown("""
- **LLM:** Llama 3.3 70B Instruct AWQ via vLLM on **ACE HPC** (A100 80GB)
- **Embeddings:** nomic-embed-text (Ollama, local)
- **Vector DB:** ChromaDB (local)
- **Orchestration:** LangGraph
- **Frontend:** Streamlit
""")

    st.markdown("---")
    st.caption("MVP v0.1 · Runs entirely locally · No API keys needed")

    # ── Past Sessions ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="sidebar-section">Past Sessions</div>', unsafe_allow_html=True)
    past = load_sessions()
    if not past:
        st.caption("No saved sessions yet. Run a query to start.")
    else:
        for s in past[:10]:  # Show the 10 most recent
            ts_label = s.get("timestamp", "")[:16].replace("T", " ")
            q_short   = s.get("question", "")[:55] + ("…" if len(s.get("question", "")) > 55 else "")
            with st.expander(f"🕐 {ts_label}  —  {q_short}"):
                st.markdown(f"**Q:** {s['question']}")
                st.markdown("**Answer:**")
                # Show only the main answer (before disclaimer separator)
                full_ans = s.get("final_answer", "")
                main = full_ans.rsplit("\n\n---\n", 1)[0] if "\n\n---\n" in full_ans else full_ans
                st.markdown(main)
                st.download_button(
                    label="⬇️ Download",
                    data=s.get("final_answer", ""),
                    file_name=f"policylens_{ts_label.replace(' ', '_')}.txt",
                    mime="text/plain",
                    key=f"dl_{s.get('timestamp','')}",
                )

        # ── Clear Sessions ─────────────────────────────────────────────────
        st.markdown("---")
        if st.button("🗑️ Clear all saved sessions", use_container_width=True, type="secondary"):
            st.session_state.confirm_clear_sessions = True

        if st.session_state.get("confirm_clear_sessions"):
            st.warning("Delete all saved session files? This cannot be undone.")
            c1, c2 = st.columns(2)
            if c1.button("Yes, delete", key="confirm_clear_sessions_yes", use_container_width=True):
                deleted = 0
                for f in Path(SESSIONS_DIR).glob("*.json"):
                    f.unlink()
                    deleted += 1
                st.session_state.confirm_clear_sessions = False
                st.success(f"Deleted {deleted} session(s).")
                st.rerun()
            if c2.button("Cancel", key="confirm_clear_sessions_no", use_container_width=True):
                st.session_state.confirm_clear_sessions = False
                st.rerun()


# ---------------------------------------------------------------------------
# Main tabs: About + PolicyLens
# ---------------------------------------------------------------------------
about_tab, app_tab = st.tabs(["ℹ️ About", "⚖️ PolicyLens"])


# ---------------------------------------------------------------------------
# ABOUT TAB
# ---------------------------------------------------------------------------
with about_tab:
    st.markdown("""
    <div class="hero">
      <h1>⚖️ PolicyLens</h1>
      <p>Agentic RAG for cross-country African data protection law and policy analysis.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="about-card">
      <h3>What is PolicyLens?</h3>
      <p>
        PolicyLens is a locally-run <strong>agentic RAG (Retrieval-Augmented Generation)</strong> tool
        designed to answer complex, multi-jurisdiction questions about African data protection laws
        and related policy/governance frameworks.
      </p>
      <p>
        Unlike standard RAG (one search → one answer), PolicyLens uses a three-stage pipeline:
        it <strong>plans</strong> sub-questions per country or policy scope, <strong>retrieves</strong> and
        <strong>evaluates</strong> legal passages iteratively, and then <strong>synthesizes</strong> a formal,
        cited answer.
      </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="about-card">
      <h3>How it works</h3>
      <ol>
        <li><strong>Planner</strong> — breaks your question into targeted sub-questions, one per country or policy scope.</li>
        <li><strong>Retriever + Evaluator</strong> — searches ChromaDB per scope, checks whether the retrieved passages actually answer the sub-question, and rewrites the query with legal synonyms if needed (up to 2 retries).</li>
        <li><strong>Synthesizer</strong> — combines all retrieved context into a single, structured answer with specific section and document citations.</li>
      </ol>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="about-card">
      <h3>Knowledge base</h3>
      <p>
        The vector store contains <strong>1,450 chunks</strong> from 17 documents across binding laws,
        continental strategies, regional frameworks, and international policy/governance guidance.
      </p>
    </div>
    """, unsafe_allow_html=True)

    kb_data = []
    for filename, meta in DOCUMENTS.items():
        kb_data.append({"Scope": meta["country"], "Document": meta["document_name"], "Type": meta["document_type"]})
    st.dataframe(kb_data, use_container_width=True, hide_index=True)

    st.markdown("""
    <div class="about-card">
      <h3>Sample questions</h3>
      <p>Click any of these preset questions in the <strong>PolicyLens</strong> tab to run them through the full pipeline:</p>
      <ol>
    """, unsafe_allow_html=True)
    for q in DEMO_QUESTIONS:
        st.markdown(f"<li>{q}</li>", unsafe_allow_html=True)
    st.markdown("</ol></div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="about-card">
      <h3>Tech stack</h3>
      <ul>
        <li><strong>LLM:</strong> Llama 3.3 70B Instruct AWQ via vLLM on <strong>ACE HPC</strong> (A100 80GB)</li>
        <li><strong>Embeddings:</strong> nomic-embed-text via Ollama (local)</li>
        <li><strong>Vector store:</strong> ChromaDB (local persistent)</li>
        <li><strong>Orchestration:</strong> LangGraph</li>
        <li><strong>Frontend:</strong> Streamlit</li>
      </ul>
      <p><em>MVP v0.1 · Runs entirely locally · No API keys needed</em></p>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# POLICYLENS TAB
# ---------------------------------------------------------------------------
with app_tab:
    st.markdown("""
    <div class="hero">
      <h1>⚖️ PolicyLens</h1>
      <p>Ask complex multi-jurisdiction questions and get formally cited answers.</p>
    </div>
    """, unsafe_allow_html=True)

    # Preset question buttons
    st.markdown('<div class="section-header">Preset Demo Questions</div>', unsafe_allow_html=True)
    st.caption("Click any question below to run it through the full agentic pipeline.")

    btn_labels = [
        ("🔀", "Compare SA & Kenya", "Data sharing alignment & conflicts for research"),
        ("🏥", "Health data: SA & Nigeria", "Safeguards for sharing health data"),
        ("🌍", "Multi-country gap analysis", "Legal mechanisms & gaps across SA, Kenya, Nigeria"),
        ("🏛️", "National vs AU Malabo", "Common themes & divergences with continental framework"),
    ]

    # If a follow-up question was selected from a previous analysis, replay it
    follow_up_question = st.session_state.pop("next_question", None)

    col1, col2 = st.columns(2, gap="medium")
    selected_question = follow_up_question

    with col1:
        for i in [0, 2]:
            emoji, label, caption = btn_labels[i]
            if st.button(f"{emoji}  {label}\n{caption}", key=f"btn_{i}", use_container_width=True):
                selected_question = DEMO_QUESTIONS[i]

    with col2:
        for i in [1, 3]:
            emoji, label, caption = btn_labels[i]
            if st.button(f"{emoji}  {label}\n{caption}", key=f"btn_{i}", use_container_width=True):
                selected_question = DEMO_QUESTIONS[i]

    # Custom question input
    st.markdown('<div class="section-header">Ask Your Own Question</div>', unsafe_allow_html=True)

    custom_question = st.text_area(
        label="custom_q",
        label_visibility="collapsed",
        height=90,
        placeholder=(
            "e.g., What are the consent requirements for processing health data "
            "across Nigeria and Kenya, and how do they compare to the Malabo Convention?"
        )
    )

    if st.button("🚀  Ask PolicyLens", type="primary", use_container_width=True):
        if custom_question.strip():
            selected_question = custom_question.strip()
        else:
            st.warning("Please enter a question before clicking Ask.")

    # Pipeline execution + live log display
    if selected_question:

        st.markdown(
            f'<div class="question-banner">📌 {selected_question}</div>',
            unsafe_allow_html=True
        )

        # Run the agentic pipeline once before rendering the UI panels
        with st.spinner("Running agentic pipeline..."):
            result = run_query(selected_question)

        # Persist the completed session to disk
        save_session(selected_question, result)

        # Helper to render the log box inside the collapsible log section
        def render_log(lines: list, placeholder):
            """Re-renders the log box with all lines collected so far."""
            formatted = []
            for line in lines:
                # Apply colour classes based on content
                if line.startswith("📋"):
                    formatted.append(f'<span class="log-stage">{line}</span>')
                elif line.startswith("🔍"):
                    formatted.append(f'<span class="log-search">{line}</span>')
                elif line.startswith("✅"):
                    formatted.append(f'<span class="log-ok">{line}</span>')
                elif line.startswith("⚠️"):
                    formatted.append(f'<span class="log-warn">{line}</span>')
                elif line.startswith("🔄"):
                    formatted.append(f'<span class="log-rewrite">{line}</span>')
                elif line.startswith("📝"):
                    formatted.append(f'<span class="log-synth">{line}</span>')
                else:
                    formatted.append(line)
            html = "<br>".join(formatted)
            placeholder.markdown(
                f'<div class="log-box">{html}</div>',
                unsafe_allow_html=True
            )

        # -------------------------------------------------------------------
        # Analysis panel (top, expanded by default)
        # -------------------------------------------------------------------
        with st.expander("📊 Analysis", expanded=True):
            st.markdown('<div class="section-header">Analysis</div>', unsafe_allow_html=True)
            answer = result.get("final_answer", "No answer was generated.")

            # Split disclaimer from the main answer for separate rendering
            if "\n\n---\n" in answer:
                main_answer, disclaimer = answer.rsplit("\n\n---\n", 1)
            else:
                main_answer, disclaimer = answer, ""

            # Convert the LLM's markdown to HTML, then inject it inside the styled card div.
            # Splitting the open/close tags across separate st.markdown() calls does NOT work
            # because each call is its own DOM element — Streamlit never merges them.
            answer_html = md.markdown(main_answer, extensions=["nl2br", "tables"])
            st.markdown(
                f'<div class="answer-card">{answer_html}</div>',
                unsafe_allow_html=True
            )

            if disclaimer:
                st.caption(disclaimer.strip().lstrip("*").rstrip("*"))

            # Download button
            st.download_button(
                label="⬇️  Download analysis as .txt",
                data=answer,
                file_name="policylens_analysis.txt",
                mime="text/plain",
                use_container_width=True
            )

        # -------------------------------------------------------------------
        # Follow-up questions panel
        # -------------------------------------------------------------------
        follow_ups = result.get("follow_up_questions", [])
        if follow_ups:
            with st.expander("💡 Suggested Follow-up Questions", expanded=True):
                st.markdown('<div class="section-header">Suggested Follow-up Questions</div>', unsafe_allow_html=True)
                st.caption("Click any question to run it through the pipeline.")
                for i, q in enumerate(follow_ups, 1):
                    if st.button(f"{i}. {q}", key=f"follow_up_{i}", use_container_width=True):
                        st.session_state.next_question = q
                        st.rerun()

        # -------------------------------------------------------------------
        # Agent Activity Log panel (bottom, collapsed by default)
        # -------------------------------------------------------------------
        with st.expander("🤖 Agent Activity Log", expanded=False):
            st.markdown('<div class="section-header">Agent Activity Log</div>', unsafe_allow_html=True)

            log_placeholder = st.empty()
            collected_log = result.get("process_log", [])
            render_log(collected_log, log_placeholder)

            # Step count metrics
            searches = sum(1 for l in collected_log if l.startswith("🔍"))
            retries  = sum(1 for l in collected_log if l.startswith("🔄"))
            m1, m2, m3 = st.columns(3)
            m1.metric("Sub-questions", len(result.get("sub_questions", [])))
            m2.metric("Searches run", searches)
            m3.metric("Query rewrites", retries)
