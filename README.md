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
