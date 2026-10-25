# Local RAG Chatbot

A fully local Retrieval-Augmented Generation (RAG) chatbot with an **admin portal** (upload documents) and a **user portal** (ChatGPT-style chat). No paid APIs: LLM and embeddings run locally through Ollama.

Built as a learning project to understand RAG end to end: ingest, chunk, embed, retrieve, generate, evaluate.

## Architecture

```
Admin (Streamlit) ──HTTP──┐
                          ├──> FastAPI ──> Markdown KB (data/kb/*.md)
User  (Streamlit) ──HTTP/SSE┘      │──> ChromaDB (vectors)
                                   │──> SQLite (users, docs, chat history)
                                   └──> Ollama (embeddings + LLM)
```

- Browser to Streamlit uses Streamlit's internal websocket.
- Streamlit to FastAPI is plain HTTP (REST), with JWT auth.
- Chat answers stream token by token over Server-Sent Events (SSE).

## Stack

| Layer | Choice |
|---|---|
| LLM | Ollama, `llama3.2:3b` (CPU) |
| Embeddings | Ollama, `nomic-embed-text` |
| Vector DB | ChromaDB (persistent) |
| App DB | SQLite via SQLAlchemy |
| Backend | FastAPI |
| UI | Streamlit (admin and user apps) |
| Doc to Markdown | `markitdown` |
| Auth | JWT, admin and user roles |

## Project structure (planned)

```
app/
  config.py, db.py, models.py, auth.py
  ingestion/   to_markdown.py, md_chunker.py, pipeline.py
  rag/         embeddings.py, vectorstore.py, retriever.py, prompt.py, generator.py
  api/         main.py, routes_admin.py, routes_chat.py
frontend/      admin_app.py, user_app.py
eval/          qa_set.json, run_eval.py
tests/
```

## Setup

Requires Python 3.12 and [Ollama](https://ollama.com).

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt   # added as phases progress

ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

## Phases

Status: `[ ]` todo, `[x]` done.

### Phase 0: Environment
- [x] Virtual environment
- [ ] Ollama installed, models pulled
- [ ] Git repo and GitHub remote

### Phase 1: Ingestion
Any uploaded file becomes Markdown, and the Markdown KB is what gets embedded.
- [ ] Call the embedding model by hand, inspect vectors, compute cosine similarity
- [ ] Convert files (pdf, docx, pptx, xlsx, html, txt) to `.md` with markitdown
- [ ] Heading-aware chunker (about 500 tokens, 50 overlap, heading path as metadata)
- [ ] Embed chunks and store in ChromaDB with doc id metadata

### Phase 2: Retrieval and generation (CLI)
- [ ] Top-k similarity search
- [ ] Prompt template: answer only from context, otherwise say "I don't know"
- [ ] Generate with Ollama and show source citations

### Phase 3: Backend API
- [ ] SQLAlchemy models: User, Document, ChatSession, Message
- [ ] JWT auth with admin and user roles
- [ ] Admin endpoints: upload, list, delete (also removes vectors), reindex
- [ ] Fake-token SSE endpoint first, then real streaming chat from Ollama
- [ ] Persist chat history

### Phase 4: Frontends
- [ ] Admin portal: login, upload, document list and status, delete, reindex
- [ ] User portal: login, ChatGPT-style chat with token streaming, source expander, session list

### Phase 5: Retrieval improvements
- [ ] Conversation-aware query rewriting
- [ ] Hybrid search (BM25 + vector) and reranking
- [ ] Metadata filters

### Phase 6: Evaluation
Retrieval and generation are evaluated separately.
- [ ] Golden set of 30 to 50 questions (about 5 unanswerable) in `eval/qa_set.json`
- [ ] Retrieval metrics: hit-rate@k, MRR, recall@k for k = 1, 3, 5
- [ ] Generation metrics: faithfulness, answer correctness, refusal accuracy (local LLM judge, spot-checked by hand)
- [ ] Experiments, one variable at a time: chunk size, overlap, top-k, vector vs hybrid, reranker, model size
- [ ] Regression test that fails if hit-rate@5 drops below a threshold

### Phase 7: Polish
- [ ] Tests (chunker, conversion, auth, API with mocked LLM)
- [ ] Docker / compose (optional)
- [ ] Architecture diagram, screenshots, results table

## Possible extensions
- WebSocket chat (cancel generation mid-stream)
- Larger or cloud models for comparison in evaluation
