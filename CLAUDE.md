# CLAUDE.md — AI Document Assistant (Production RAG App)

## Project Overview
Build a production-grade AI Document Assistant — users upload PDF/Word/PPT documents and ask questions. The app uses RAG (Retrieval Augmented Generation) with hybrid search, CrossEncoder reranking, and streaming LLM responses.

## Tech Stack
- Backend: FastAPI + Python 3.10+
- LLM: Groq API (llama3-8b-8192) — free
- Embeddings: sentence-transformers (BAAI/bge-small-en)
- Vector DB: ChromaDB (persistent, local)
- Keyword Search: BM25 (rank_bm25)
- Reranking: CrossEncoder (cross-encoder/ms-marco-MiniLM-L-6-v2)
- Cache: Redis (Upstash free tier)
- Database: SQLite (SQLAlchemy ORM)
- Auth: JWT (python-jose)
- Frontend: React 18 + React Router v6 + Tailwind CSS + Axios
- Deploy: Docker + Docker Compose

## Folder Structure
```
ai-doc-assistant/
├── backend/
│   ├── main.py                  # FastAPI app + CORS + lifespan
│   ├── config.py                # env variables (pydantic BaseSettings)
│   ├── database.py              # SQLAlchemy engine + session + Base
│   ├── auth/
│   │   ├── models.py            # User SQLAlchemy model
│   │   ├── schemas.py           # Pydantic schemas (UserCreate, UserLogin, TokenResponse)
│   │   ├── routes.py            # POST /auth/register, POST /auth/login
│   │   ├── jwt_handler.py       # create_token, verify_token
│   │   └── dependencies.py      # get_current_user dependency
│   ├── documents/
│   │   ├── models.py            # Document SQLAlchemy model
│   │   ├── schemas.py           # DocumentResponse, UploadResponse
│   │   ├── routes.py            # POST /docs/upload, GET /docs/list, DELETE /docs/{id}
│   │   ├── parser.py            # PDF (pypdf), Word (python-docx), PPT (python-pptx)
│   │   └── chunker.py           # RecursiveCharacterTextSplitter (500 chars, 80 overlap)
│   ├── rag/
│   │   ├── routes.py            # POST /chat (streaming SSE), GET /chat/history/{session_id}
│   │   ├── embeddings.py        # HuggingFace BGE embedding service
│   │   ├── vector_store.py      # ChromaDB persistent client + collection
│   │   ├── bm25_search.py       # BM25Okapi keyword search
│   │   ├── retriever.py         # HybridRetriever (vector + BM25 + RRF merge)
│   │   ├── reranker.py          # CrossEncoder reranking
│   │   ├── generator.py         # AsyncGroq streaming + system prompt
│   │   ├── cache.py             # Redis cache-aside pattern (TTL 1 hour)
│   │   └── schemas.py           # ChatRequest, ChatHistoryResponse
│   ├── chat_history/
│   │   ├── models.py            # ChatSession, ChatMessage SQLAlchemy models
│   │   └── service.py           # save/get chat history
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Routes setup
│   │   ├── api/
│   │   │   └── api.js           # Axios instance + request/response interceptors
│   │   ├── hooks/
│   │   │   ├── useAuth.js       # login, logout, token management
│   │   │   └── useStreamChat.js # SSE streaming hook
│   │   ├── pages/
│   │   │   ├── Login.jsx        # Login + Register form
│   │   │   ├── Dashboard.jsx    # Document upload + list
│   │   │   └── Chat.jsx         # Chat interface
│   │   ├── components/
│   │   │   ├── ProtectedRoute.jsx  # Auth check wrapper
│   │   │   ├── FileUpload.jsx      # Drag & drop upload
│   │   │   ├── DocumentList.jsx    # Uploaded docs list
│   │   │   ├── ChatWindow.jsx      # Messages display
│   │   │   ├── MessageBubble.jsx   # User/AI message
│   │   │   ├── StreamingText.jsx   # Typing animation
│   │   │   └── Sidebar.jsx         # Chat history list
│   │   └── index.css            # Tailwind imports
│   ├── tailwind.config.js
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Backend Requirements

### Authentication
- POST /auth/register — email, password, name. Hash password with bcrypt. Return JWT token.
- POST /auth/login — email, password. Verify. Return JWT token with user info.
- JWT token — HS256, 24 hour expiry, payload: {user_id, email, role}.
- Dependency: get_current_user — extract and verify token from Authorization header.

### Document Management
- POST /docs/upload — multipart file upload. Accept PDF, DOCX, PPTX only. Max 10MB.
- Parse document content:
  - PDF: pypdf.PdfReader — extract text page by page
  - DOCX: python-docx — extract paragraphs
  - PPTX: python-pptx — extract slide text
- Chunk with RecursiveCharacterTextSplitter: chunk_size=500, chunk_overlap=80
- Each chunk gets metadata: {doc_id, filename, page_number, chunk_index, user_id}
- Embed chunks with BAAI/bge-small-en (384 dimensions)
- Store in ChromaDB persistent collection
- Store BM25 corpus for keyword search
- Save document record in SQLite (id, filename, user_id, chunk_count, created_at)
- GET /docs/list — return user's uploaded documents
- DELETE /docs/{id} — delete document + its chunks from ChromaDB + BM25

### RAG Chat
- POST /chat — StreamingResponse with text/event-stream
- Request body: {query: str, session_id: str (optional)}
- Flow:
  1. Check Redis cache — key: hash of query. If HIT, stream cached answer.
  2. Hybrid search:
     - ChromaDB vector search (top 10)
     - BM25 keyword search (top 10)
     - Reciprocal Rank Fusion merge (k=60)
  3. CrossEncoder rerank — top 5 results
  4. Build context — join top 5 chunks, max 12000 chars
  5. Groq AsyncClient streaming:
     - model: llama3-8b-8192
     - temperature: 0.1
     - System prompt: "You are a helpful document assistant. Answer ONLY from provided context. If answer not in context, say so. Be concise."
  6. Stream tokens via SSE: yield f"data: {token}\n\n"
  7. End signal: yield "data: [DONE]\n\n"
  8. After streaming complete: save full answer to Redis cache (TTL: 3600s)
  9. Save to chat history (session_id, query, answer)

### Chat History
- GET /chat/history/{session_id} — return messages for session
- Each message: {role: "user"|"ai", content: str, timestamp: str}

### Redis Caching
- Cache-aside pattern
- Key: f"chat:{hashlib.md5(query.encode()).hexdigest()}"
- TTL: 3600 seconds (1 hour)
- On document delete: clear related cache keys

### CORS
- Allow origins: ["http://localhost:3000", "http://localhost:5173"]
- Allow methods: ["*"]
- Allow headers: ["*"]

## Frontend Requirements

### Routing (React Router v6)
- / → redirect to /login
- /login → Login/Register page
- /dashboard → Document upload + list (protected)
- /chat → Chat interface (protected)
- /chat/:sessionId → Specific chat session (protected)

### Axios Setup (api.js)
- baseURL from env: VITE_API_URL || "http://localhost:8000"
- Request interceptor: auto add JWT token from localStorage
- Response interceptor: 401 → remove token → redirect /login

### Pages
- Login.jsx: email + password form. Toggle login/register. On success: store token, redirect /dashboard.
- Dashboard.jsx: file upload area (drag & drop or click). List of uploaded documents with delete button. "New Chat" button → /chat.
- Chat.jsx: sidebar with chat history sessions. Main area: messages + input. Streaming display with typing cursor. Auto scroll to bottom.

### Streaming (useStreamChat hook)
- fetch with ReadableStream
- Parse SSE "data: " lines
- setState append tokens to last AI message
- Handle [DONE] signal

### Styling
- Tailwind CSS
- Dark/light theme support
- Mobile responsive
- Clean, professional UI — similar to ChatGPT

## Docker

### backend/Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### frontend/Dockerfile
```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

### docker-compose.yml
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: ./backend/.env
    volumes:
      - chroma_data:/app/chroma_db
  frontend:
    build: ./frontend
    ports: ["3000:80"]
    depends_on: [backend]
volumes:
  chroma_data:
```

## Build Order
1. backend/config.py + database.py + main.py (skeleton)
2. auth/ (register, login, JWT, dependency)
3. documents/ (upload, parse, chunk)
4. rag/embeddings.py + vector_store.py (ChromaDB setup)
5. rag/bm25_search.py (keyword search)
6. rag/retriever.py (hybrid search + RRF)
7. rag/reranker.py (CrossEncoder)
8. rag/generator.py (Groq streaming)
9. rag/cache.py (Redis)
10. rag/routes.py (chat endpoint — tie everything)
11. chat_history/ (save/get)
12. Frontend: api.js + useAuth + Login
13. Frontend: Dashboard + FileUpload
14. Frontend: Chat + useStreamChat + streaming display
15. Docker setup + docker-compose
16. Testing + README

## Important Rules
- Use async/await everywhere — FastAPI async endpoints
- Pydantic v2 for all schemas
- SQLAlchemy 2.0 style
- Error handling — try/except with proper HTTP status codes
- .env for all secrets — never hardcode
- Type hints on all functions
- Docstrings on all classes and key functions