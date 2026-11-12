# AI Document Assistant

Upload PDF / Word / PowerPoint files and ask questions about them. Answers are generated with RAG:
hybrid search (ChromaDB vectors + BM25, merged with Reciprocal Rank Fusion), CrossEncoder reranking,
and streaming responses from Groq.

**Stack:** FastAPI · MySQL (SQLAlchemy 2.0 async) · ChromaDB · BM25 · sentence-transformers · Groq · Redis · React 18 + Tailwind

## Configuration

Create `backend/.env` (see `backend/.env.example`):

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key |
| `GROQ_MODEL` | Optional, default `openai/gpt-oss-20b` (`llama3-8b-8192` was decommissioned by Groq) |
| `REDIS_URL` | e.g. `rediss://default:<password>@<host>:6379` (Upstash). Cache is optional: if Redis is unreachable, chat still works |
| `DATABASE_URL` | e.g. `mysql+pymysql://user:pass@localhost:3306/ai_doc_assistant` |
| `JWT_SECRET` | Long random string |

For Docker, also set `MYSQL_ROOT_PASSWORD` in a project-root `.env`.
Never commit `.env` files.

## Run locally

1. Create the database: `CREATE DATABASE ai_doc_assistant;`
2. Backend:
   ```bash
   cd backend
   pip install -r requirements.txt
   python main.py            # http://localhost:8000  (API docs at /docs)
   ```
   Tables are created on startup. The first upload downloads the embedding model and the first
   question downloads the reranker model.
3. Frontend:
   ```bash
   cd frontend
   npm install
   npm run dev               # http://localhost:5173
   ```

## Run with Docker

> **Status: untested.** The Dockerfiles and `docker-compose.yml` have been written but never built or
> run. The local (non-Docker) setup above is the one that has been verified end to end.

```bash
docker compose up --build   # app on http://localhost:3000, API on http://localhost:8000
```

Compose starts MySQL, the backend and the frontend, and overrides `DATABASE_URL` to point at the
MySQL container.

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

The tests cover RRF, chunking, JWT, BM25, document parsing and the SSE helpers. They need no
database, Redis or API keys.

## API

| Method | Path | Notes |
|---|---|---|
| POST | `/auth/register`, `/auth/login` | Return a JWT and user info |
| GET | `/auth/me` | Current user |
| POST | `/docs/upload` | PDF/DOCX/PPTX, max 10MB |
| GET | `/docs/list` | Your documents |
| DELETE | `/docs/{id}` | Removes the document, its vectors and BM25 entries, and clears your cached answers |
| POST | `/chat` | `{query, session_id?}` → `text/event-stream`; session id in the `X-Session-Id` header |
| GET | `/chat/sessions` | Your chat sessions |
| GET | `/chat/history/{session_id}` | Messages of a session |

### Streaming format

Each token is sent as `data: <token>`. A token containing newlines is split across several `data:`
lines; clients rejoin them with `\n`. The stream ends with `data: [DONE]`; failures send
`data: [ERROR] <message>` first.

## Notes

- Cached answers are keyed per user (`chat:{user_id}:{md5(query)}`) so one user never receives an
  answer built from another user's documents. They expire after one hour.
- Scanned PDFs without a text layer are rejected (no OCR).
- AI answers are rendered as markdown in the chat UI (bold, lists, links, code blocks). Raw HTML in
  an answer is not rendered.
- Timestamps are stored in UTC; the frontend converts them to the browser's local time.
- Verified so far: backend tests, and in a browser: register, login, DOCX / PDF / PPTX upload (click
  and drag-and-drop), streaming chat with correct answers from each file type, delete, the dark
  theme toggle, the mobile sidebar and the redirect to login on an invalid token. Not yet verified:
  Docker.
