# meeting-notes-tracker

Take notes during a meeting and attach a relevant image to them. The front end is
React/Vite; the API is Go deployed with Encore; note images come from the Pexels API.

## Endpoints

| Method | Path | Job |
| --- | --- | --- |
| `GET` | `/note/:id` | Fetch a note by id |
| `POST` | `/note` | Create or update a note |
| `GET` | `/images/:query` | Search Pexels for a note image |

## Stack

- Front end: React + Vite + TypeScript + Tailwind (`frontend/`)
- API: Go; `note/` and `pexels/` are Encore services
- Storage: cloud SQL database provisioned through Encore
- Infrastructure: Encore handles provisioning and service tracking

## Layout

```
frontend/    React/Vite app
note/        Encore service - note CRUD
pexels/      Encore service - image search
encore.app
```

## Run it

Backend (Encore CLI required):

```
encore run
```

Front end:

```
cd frontend
npm install
npm run dev
```

## Agent service (`ai/`)

A Python sidecar for the Go API: `note/` keeps owning note storage, the sidecar
owns everything semantic.

```
START -> normalise -+-> summarise -------+
                    |                    +-> index -> END
                    +-> extract_actions -+
```

- **Parallel readings** - the summary and the action items come off the same normalised text, in parallel
- **Action items** - returned as `{owner, action, due}` objects; the parser recovers the JSON even when the model wraps it in prose
- **Searchable** - the note is embedded into Qdrant so `/query` can answer across notes with citations
- **Models** - vLLM (`Qwen/Qwen3-32B` chat, `BAAI/bge-m3` embeddings)

```
docker compose -f ai/docker-compose.ai.yml up
```

`POST /process` summarises and indexes a note; `POST /query` searches across them.
See [`ai/README.md`](ai/README.md).
