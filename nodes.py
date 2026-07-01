"""
nodes.py
--------
PolicyLens — LangGraph node functions.

Each function corresponds to a node in the agentic RAG graph.
Functions receive the full state dict and return a dict of
fields to update.
"""

import json
import re
import sys
from langchain_openai import ChatOpenAI  # vLLM exposes an OpenAI-compatible API
from langchain_core.messages import SystemMessage, HumanMessage
from retrieval import get_vectorstore, search_by_country, search_all, format_context
from config import LLM_MODEL, LLM_TEMPERATURE, MAX_RETRIES, TOP_K, VLLM_BASE_URL


# ---------------------------------------------------------------------------
# Initialise shared resources (loaded once, reused across calls)
# ---------------------------------------------------------------------------
# ChatOpenAI with openai_api_key="EMPTY" is the standard way to call a vLLM
# server — the key is required by the client but ignored server-side.
llm = ChatOpenAI(
    model=LLM_MODEL,
    temperature=LLM_TEMPERATURE,
    base_url=VLLM_BASE_URL,
    openai_api_key="EMPTY",  # vLLM does not enforce auth; value is required but ignored
)
vectorstore = get_vectorstore()


# ---------------------------------------------------------------------------
# Helper: console print that always flushes (works on Windows)
# ---------------------------------------------------------------------------
def _log(msg: str):
    """Prints a message to stdout, flushing immediately so it appears in real time."""
    print(msg, flush=True)


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
    _log("\n" + "=" * 60)
    _log("[STAGE 1] PLANNER")
    _log("=" * 60)
    _log(f"  Question: {state['user_question']}")
    _log("  Sending to LLM to generate research plan...")

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
        _log("  WARNING: Could not parse JSON plan — falling back to broad search.")
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

    _log(f"\n  Reasoning: {plan.get('reasoning', 'N/A')}")
    _log(f"  Identified {len(sub_questions)} sub-question(s):")
    for i, sq in enumerate(sub_questions, 1):
        _log(f"    {i}. [{sq['target_country']}] {sq['question']}")

    # Build process log entries
    log = [f"📋 **Planning complete** — {len(sub_questions)} sub-questions identified"]
    log.append(f"*Reasoning: {plan.get('reasoning', '')}*")
    for i, sq in enumerate(sub_questions, 1):
        log.append(f"**{i}.** `[{sq['target_country']}]` {sq['question']}")

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
    total = len(state["sub_questions"])

    _log(f"\n[STAGE 2 — Sub-question {idx+1}/{total}] RETRIEVER")
    _log(f"  Country filter : {target_country}")
    _log(f"  Search query   : {query[:100]}{'...' if len(query) > 100 else ''}")

    # Perform the search
    if target_country == "all":
        results = search_all(vectorstore, query, top_k=TOP_K)
    else:
        results = search_by_country(vectorstore, query, target_country, top_k=TOP_K)

    _log(f"  Retrieved      : {len(results)} passages")
    for i, (doc, score) in enumerate(results, 1):
        _log(f"    Passage {i}: relevance={score:.3f} | "
             f"section='{doc.metadata.get('section_heading','?')[:50]}' | "
             f"pages {doc.metadata.get('start_page','?')}-{doc.metadata.get('end_page','?')}")

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

    short_query = query[:70] + "..." if len(query) > 70 else query
    log_entry = (
        f"🔍 **Searching `{target_country}`** — *\"{short_query}\"*\n"
        f"  → Retrieved **{len(results)} passages**"
    )

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

    _log(f"\n  [EVALUATOR] Checking sufficiency for sub-question {idx+1}...")

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

    _log(f"  [EVALUATOR] Verdict: {status}")
    # Print the evaluator's reasoning (first 200 chars)
    reasoning_preview = response.content.strip()[:200]
    _log(f"  [EVALUATOR] Reasoning: {reasoning_preview}...")

    if status == "SUFFICIENT":
        log_entry = f"✅ **Context check:** SUFFICIENT for `{sq['target_country']}`"
    else:
        log_entry = f"⚠️ **Context check:** INSUFFICIENT for `{sq['target_country']}` — retrying with rewritten query"

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
    retry_count = state.get("retry_count", 0) + 1

    _log(f"\n  [REWRITER] Generating alternative query (attempt {retry_count}/{MAX_RETRIES})...")

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

    _log(f"  [REWRITER] New query: {new_query}")

    short_query = new_query[:70] + "..." if len(new_query) > 70 else new_query
    log_entry = f"🔄 **Query rewrite** (attempt {retry_count}): *\"{short_query}\"*"

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
    total = len(state["sub_questions"])

    _log(f"\n  [ADVANCE] Sub-question {state['current_sub_question_index']+1} complete.")

    # Reset query to the next sub-question's text (if there is one)
    if next_idx < total:
        next_query = state["sub_questions"][next_idx]["question"]
        _log(f"  [ADVANCE] Moving to sub-question {next_idx+1}/{total}")
    else:
        next_query = ""
        _log(f"  [ADVANCE] All sub-questions processed — proceeding to synthesis.")

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
    _log("\n" + "=" * 60)
    _log("[STAGE 3] SYNTHESIZER")
    _log("=" * 60)
    total_chunks = sum(
        len(v.split("---")) for v in state["retrieved_chunks"].values()
    )
    _log(f"  Synthesizing answer from {len(state['sub_questions'])} sub-question(s), "
         f"~{total_chunks} passage block(s)...")

    system_prompt = load_prompt("synthesizer.txt")
    user_question = state["user_question"]

    # Build grounded context blocks — each sub-question gets a clearly labelled section
    # with its own passage numbers so the synthesizer knows exactly what evidence is
    # available per country and cannot bleed citations across sections.
    full_context_parts = []
    passage_offset = 0  # Track global passage numbers across sub-questions
    for i, sq in enumerate(state["sub_questions"]):
        raw_context = state["retrieved_chunks"].get(str(i), "")

        if not raw_context or raw_context.startswith("No passages met"):
            # No usable evidence for this sub-question — tell the LLM explicitly
            block = (
                f"═══ BLOCK {i+1}: {sq['target_country'].upper()} ═══\n"
                f"Sub-question: {sq['question']}\n"
                f"Evidence: No sufficiently relevant passages were retrieved. "
                f"Do NOT fabricate provisions for this country.\n"
            )
        else:
            # Renumber passages sequentially so the LLM can cite them unambiguously
            chunks = raw_context.split("\n\n---\n\n")
            renumbered = []
            for j, chunk in enumerate(chunks):
                global_num = passage_offset + j + 1
                # Replace "[Passage N]" with the global passage number
                chunk = re.sub(r"\[Passage \d+\]", f"[Passage {global_num}]", chunk, count=1)
                renumbered.append(chunk)
            passage_offset += len(chunks)

            block = (
                f"═══ BLOCK {i+1}: {sq['target_country'].upper()} ═══\n"
                f"Sub-question: {sq['question']}\n"
                f"Available passages: {passage_offset - len(chunks) + 1}–{passage_offset}\n\n"
                + "\n\n---\n\n".join(renumbered)
            )

        full_context_parts.append(block)

    full_context = "\n\n".join(full_context_parts)

    log_entry = "📝 **Synthesizing** final answer from all retrieved context..."

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=(
            f"Original user question: {user_question}\n\n"
            f"Research findings (organised by country block):\n\n{full_context}\n\n"
            f"IMPORTANT: Only cite passages that appear in the blocks above. "
            f"If a block says 'Do NOT fabricate', state that information was unavailable "
            f"for that country rather than inventing provisions.\n\n"
            f"Please provide a comprehensive, formal answer with specific legal citations."
        ))
    ])

    final_answer = response.content.strip()

    _log(f"  Answer generated ({len(final_answer)} chars).")
    _log("\n" + "=" * 60)
    _log("  PIPELINE COMPLETE")
    _log("=" * 60)

    # Append disclaimer
    disclaimer = (
        "\n\n---\n*Disclaimer: This analysis is generated by an AI system "
        "for research purposes and does not constitute legal advice.*"
    )
    final_answer += disclaimer

    return {
        "final_answer": final_answer,
        "process_log": state.get("process_log", []) + [log_entry, "✅ **Analysis complete!**"]
    }


# ---------------------------------------------------------------------------
# STAGE 4: Follow-up Question Generator
# ---------------------------------------------------------------------------
def follow_up_node(state: dict) -> dict:
    """
    Reads the original question and final answer, then generates
    3-5 logical follow-up questions that deepen the investigation.

    Updates: follow_up_questions, process_log
    """
    _log("\n" + "=" * 60)
    _log("[STAGE 4] FOLLOW-UP QUESTION GENERATOR")
    _log("=" * 60)
    _log("  Generating follow-up questions from the analysis...")

    system_prompt = load_prompt("follow_up_generator.txt")
    user_question = state["user_question"]
    final_answer = state.get("final_answer", "")

    # Strip the disclaimer from the answer so the generator focuses on substance
    main_answer = final_answer.split("\n\n---\n")[0] if "\n\n---\n" in final_answer else final_answer

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=(
            f"Original question: {user_question}\n\n"
            f"Analysis answer:\n{main_answer}\n\n"
            f"Generate follow-up questions based on the analysis above."
        ))
    ])

    raw = response.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw)
        follow_ups = parsed.get("follow_up_questions", [])
    except json.JSONDecodeError:
        _log("  WARNING: Could not parse follow-up questions JSON — returning empty list.")
        follow_ups = []

    # Deduplicate and limit to a maximum of 5
    seen = set()
    clean = []
    for q in follow_ups:
        q = q.strip()
        if q and q not in seen and len(clean) < 5:
            clean.append(q)
            seen.add(q)

    _log(f"  Generated {len(clean)} follow-up question(s).")
    for i, q in enumerate(clean, 1):
        _log(f"    {i}. {q}")

    return {
        "follow_up_questions": clean,
        "process_log": state.get("process_log", []) + [f"💡 **Generated {len(clean)} follow-up question(s)**"]
    }
