"""LangGraph pipelines for notes.

Two graphs live here:

    process:  START -> normalise -+-> summarise -------+-> index -> END
                                  +-> extract_actions -+

    query:    START -> retrieve -> route -+-> answer  -> END
                                          +-> decline -> END

Summarising and action extraction are independent readings of the same text, so
they run in parallel and only fan in at the index step.
"""

import json
import re
from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from core import chat_model, index_note, search_notes


class NoteState(TypedDict, total=False):
    note_id: str
    title: str | None
    raw: str
    normalised: str
    summary: str
    decisions: list[str]
    actions: list[dict[str, Any]]
    indexed: int


class QueryState(TypedDict, total=False):
    question: str
    hits: list[dict[str, Any]]
    answer: str
    citations: list[dict[str, Any]]


def _json_block(raw: str) -> Any:
    """Models wrap JSON in prose and fences. Recover the object, or give up quietly."""
    text = raw.strip()
    span = re.search(r"(\{.*\}|\[.*\])", text, re.S)
    if not span:
        return None
    try:
        return json.loads(span.group(1))
    except json.JSONDecodeError:
        return None


def normalise(state: NoteState) -> dict[str, Any]:
    raw = state.get("raw", "")
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in raw.splitlines()]
    return {"normalised": "\n".join(ln for ln in lines if ln)}


def summarise(state: NoteState) -> dict[str, Any]:
    prompt = (
        "Summarise these meeting notes. Reply with JSON only:\n"
        '{"summary": "...", "decisions": ["..."]}\n\n'
        f"Notes:\n{state['normalised']}"
    )
    data = _json_block(str(chat_model().invoke(prompt).content)) or {}
    return {
        "summary": str(data.get("summary", "")).strip(),
        "decisions": list(data.get("decisions", []) or []),
    }


def extract_actions(state: NoteState) -> dict[str, Any]:
    prompt = (
        "Extract action items. Reply with a JSON array only, no prose:\n"
        '[{"owner": "...", "action": "...", "due": "..."}]\n'
        "Use null when an owner or due date is not stated.\n\n"
        f"Notes:\n{state['normalised']}"
    )
    data = _json_block(str(chat_model(max_tokens=800).invoke(prompt).content))
    actions = data if isinstance(data, list) else []
    return {"actions": [a for a in actions if isinstance(a, dict)]}


def index(state: NoteState) -> dict[str, Any]:
    count = index_note(
        state.get("note_id", "unknown"), state.get("title"), state.get("normalised", "")
    )
    return {"indexed": count}


def build_process_graph():
    g = StateGraph(NoteState)
    g.add_node("normalise", normalise)
    g.add_node("summarise", summarise)
    g.add_node("extract_actions", extract_actions)
    g.add_node("index", index)

    g.add_edge(START, "normalise")
    g.add_edge("normalise", "summarise")
    g.add_edge("normalise", "extract_actions")
    g.add_edge("summarise", "index")
    g.add_edge("extract_actions", "index")
    g.add_edge("index", END)
    return g.compile()


def retrieve(state: QueryState) -> dict[str, Any]:
    return {"hits": search_notes(state["question"])}


def _decide(state: QueryState) -> Literal["answer", "decline"]:
    return "answer" if state.get("hits") else "decline"


def answer(state: QueryState) -> dict[str, Any]:
    numbered = "\n\n".join(
        f"[{i + 1}] {h.get('text', '')}" for i, h in enumerate(state.get("hits", []))
    )
    prompt = (
        "Answer using only the numbered note excerpts and cite them as [n]. "
        "If they do not cover it, say so.\n\n"
        f"Question: {state['question']}\n\nExcerpts:\n{numbered}"
    )
    text = str(chat_model().invoke(prompt).content).strip()
    citations = [
        {
            "index": i + 1,
            "note_id": h.get("note_id"),
            "title": h.get("title"),
            "score": round(float(h.get("score", 0.0)), 4),
        }
        for i, h in enumerate(state.get("hits", []))
    ]
    return {"answer": text, "citations": citations}


def decline(state: QueryState) -> dict[str, Any]:
    return {"answer": "No indexed notes match that question.", "citations": []}


def build_query_graph():
    g = StateGraph(QueryState)
    g.add_node("retrieve", retrieve)
    g.add_node("answer", answer)
    g.add_node("decline", decline)

    g.add_edge(START, "retrieve")
    g.add_conditional_edges("retrieve", _decide, {"answer": "answer", "decline": "decline"})
    g.add_edge("answer", END)
    g.add_edge("decline", END)
    return g.compile()


PROCESS_APP = build_process_graph()
QUERY_APP = build_query_graph()


def process(note_id: str, raw: str, title: str | None = None) -> NoteState:
    return PROCESS_APP.invoke({"note_id": note_id, "raw": raw, "title": title})


def query(question: str) -> QueryState:
    return QUERY_APP.invoke({"question": question})
