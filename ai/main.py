"""HTTP surface for the notes agent. The Go `note` service calls these."""

import json
from typing import Any, AsyncIterator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core import get_settings, search_notes
from graph import PROCESS_APP, QUERY_APP, process, query

api = FastAPI(title="meeting notes agent", version="1.0.0")


class ProcessRequest(BaseModel):
    note_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    title: str | None = None


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


@api.get("/health")
def health() -> dict[str, Any]:
    s = get_settings()
    return {
        "status": "ok",
        "llm_model": s.llm_model,
        "embed_model": s.embed_model,
        "collection": s.qdrant_collection,
    }


@api.post("/process")
def process_endpoint(req: ProcessRequest) -> dict[str, Any]:
    result = process(req.note_id, req.text, req.title)
    return {
        "note_id": req.note_id,
        "summary": result.get("summary", ""),
        "decisions": result.get("decisions", []),
        "actions": result.get("actions", []),
        "indexed_chunks": result.get("indexed", 0),
    }


@api.post("/query")
def query_endpoint(req: QueryRequest) -> dict[str, Any]:
    result = query(req.question)
    return {"answer": result.get("answer", ""), "citations": result.get("citations", [])}


@api.post("/process/stream")
async def process_stream(req: ProcessRequest) -> StreamingResponse:
    async def events() -> AsyncIterator[str]:
        state: dict[str, Any] = {"note_id": req.note_id, "raw": req.text, "title": req.title}
        for step in PROCESS_APP.stream(state):
            for node, update in step.items():
                yield f"event: node\ndata: {json.dumps({'node': node, 'update': _safe(update)})}\n\n"
                state.update(update)
        yield f"event: done\ndata: {json.dumps(_safe(state))}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


@api.post("/query/stream")
async def query_stream(req: QueryRequest) -> StreamingResponse:
    async def events() -> AsyncIterator[str]:
        state: dict[str, Any] = {"question": req.question}
        for step in QUERY_APP.stream(state):
            for node, update in step.items():
                yield f"event: node\ndata: {json.dumps({'node': node, 'update': _safe(update)})}\n\n"
                state.update(update)
        yield f"event: done\ndata: {json.dumps(_safe(state))}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


def _safe(d: dict[str, Any]) -> dict[str, Any]:
    """The normalised note is the input echoed back - no need to stream all of it."""
    out = {k: v for k, v in d.items() if k != "normalised"}
    if "hits" in out:
        out["hits"] = [h.get("text", "")[:160] for h in out["hits"]]
    return out


@api.get("/search")
def quick_search(q: str) -> dict[str, Any]:
    return {"hits": search_notes(q)}
