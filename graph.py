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
    rewrite_node, advance_node, synthesize_node, follow_up_node
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

    # Stage 4 output
    follow_up_questions: list

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
    graph.add_node("follow_up", follow_up_node)

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

    graph.add_edge("synthesize", "follow_up")  # Synthesize → follow-up generator
    graph.add_edge("follow_up", END)          # Follow-up → done

    # Compile the graph
    compiled = graph.compile()
    return compiled


# ---------------------------------------------------------------------------
# Convenience function for running a query
# ---------------------------------------------------------------------------
def _initial_state(question: str) -> dict:
    """Returns a fresh initial state for the given question."""
    return {
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
        "follow_up_questions": [],
        "process_log": []
    }


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
    final_state = graph.invoke(_initial_state(question))
    return final_state


def run_query_streaming(question: str):
    """
    Streams the pipeline step-by-step, yielding (node_name, state_update)
    after each node completes. The caller can use the node_name to drive
    a live progress indicator in the UI.

    Yields:
        Tuples of (node_name: str, state_update: dict) for each executed node.
    """
    graph = build_graph()
    for chunk in graph.stream(_initial_state(question)):
        # Each chunk is {node_name: {updated_fields...}}
        for node_name, state_update in chunk.items():
            yield node_name, state_update
