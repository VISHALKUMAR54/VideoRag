import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import warn_missing_keys
from routes import chat, ingest, status, ws
from routes import metadata as metadata_route
from routes import timings as timings_route
from routes import thumbnail as thumbnail_route

# startup + shutdown lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    warn_missing_keys()
    try:
        from services.vector_store import setup_collection
        await setup_collection(recreate=False)
        print("[Startup] Qdrant collection ready")
    except Exception as e:
        print(f"[Startup] WARNING: Could not connect to Qdrant — {e}")
        print("[Startup] Start Qdrant with: docker compose up -d qdrant")

    print("[Startup] VideoRAG API ready — http://localhost:8000/docs")
    try:
        yield
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass

    print("[Shutdown] Cleaning up... done")

app = FastAPI(
    title="VideoRAG API",
    description=(
        "Full-stack RAG chatbot for comparing YouTube + Instagram videos. "
        "Powered by LangGraph, Qdrant, BGE-small embeddings, and Groq LLM."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# allow frontend on port 3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type"],
)

# register all route modules
app.include_router(ingest.router)
app.include_router(status.router)
app.include_router(chat.router)
app.include_router(ws.router)
app.include_router(metadata_route.router)
app.include_router(timings_route.router)
app.include_router(thumbnail_route.router)

@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "service": "VideoRAG API"}