# Notes agent service

Semantic sidecar for the Go API. `note/` keeps owning note storage in SQL and
`pexels/` keeps owning images; this service turns a saved note into a summary,
a list of action items, and a searchable vector.

## Graph

```
START -> normalise -+-> summarise -------+
                    |                    +-> index -> END
                    +-> extract_actions -+
```

| Node | What it does |
| --- | --- |
| `normalise` | strips filler, fixes whitespace, keeps speaker labels |
| `summarise` | short summary plus decisions made |
| `extract_actions` | owner / action / due-date triples as structured JSON |
| `index` | writes the normalised text to Qdrant so it is searchable later |
| `answer` | (query path) answers a question across notes, with citations |

Summarising and action extraction run in parallel off `normalise` - they are
independent readings of the same text.

## Stack

- LangGraph for the pipeline
- vLLM serving `Qwen/Qwen3-32B` (chat) and `BAAI/bge-m3` (embeddings)
- Qdrant for note retrieval
- FastAPI + SSE, called by the Go `note` service

## Run

```
docker compose -f ai/docker-compose.ai.yml up
```

Or standalone, against an existing vLLM and Qdrant:

```
pip install -r requirements.txt
uvicorn main:api --port 8080
```

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | liveness and resolved model names |
| `POST` | `/process` | summarise + extract actions + index a note |
| `POST` | `/query` | question answering across indexed notes, with citations |
| `POST` | `/query/stream` | same, as SSE per graph node |
| `GET` | `/search?q=` | retrieval-only debug view |

## Note

Action-item extraction asks for JSON and tolerates a model that wraps it in
prose - the parser recovers the object or returns an empty list rather than
failing the whole request.
