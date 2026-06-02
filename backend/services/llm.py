import asyncio
from typing import TypedDict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from config import (
    GROQ_API_KEY,
    HISTORY_WINDOW,
    LLM_MODEL,
    LLM_TEMPERATURE,
    REDIS_URL,
    RETRIEVAL_TOP_K,
)
from services.embedder import embed_question as _embed_question
from services.vector_store import search_both as _search_both


# state object passed between nodes
class RAGState(TypedDict):
    question:        str
    job_id:          str
    question_vector: Optional[List[float]]
    context_a:       Optional[List[dict]]
    context_b:       Optional[List[dict]]
    memory:          Optional[List[dict]]
    answer:          Optional[str]
    sources:         Optional[List[str]]


_llm: ChatGroq | None = None


# returns ChatGroq instance, loading it on first use
def _get_llm() -> ChatGroq:
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            streaming=True,
        )
    return _llm


# helper to format retrieved chunks and metadata for injection
def _format_chunks(chunks: list[dict], label: str) -> str:
    if not chunks:
        return f"No context available for Video {label}."
    
    parts = []
    first = chunks[0]
    views = first.get("views")
    likes = first.get("likes")
    comments = first.get("comments")
    followers = first.get("follower_count")
    
    views_str = f"{views:,}" if isinstance(views, (int, float)) else str(views or "unknown")
    likes_str = f"{likes:,}" if isinstance(likes, (int, float)) else str(likes or "unknown")
    comments_str = f"{comments:,}" if isinstance(comments, (int, float)) else str(comments or "unknown")
    followers_str = f"{followers:,}" if isinstance(followers, (int, float)) else "N/A"
    
    meta_info = (
        f"METADATA FOR VIDEO {label}:\n"
        f"  - Title:           {first.get('title', 'unknown')}\n"
        f"  - Creator:         {first.get('creator', 'unknown')}\n"
        f"  - Platform:        {first.get('platform', 'unknown')}\n"
        f"  - Views:           {views_str}\n"
        f"  - Likes:           {likes_str}\n"
        f"  - Comments:        {comments_str}\n"
        f"  - Engagement Rate: {first.get('engagement_rate', 0.0)}%\n"
        f"  - Upload Date:     {first.get('upload_date', 'unknown')}\n"
        f"  - Duration:        {first.get('duration_seconds', 0)}s\n"
        f"  - Followers:       {followers_str}\n"
        f"  - Hashtags:        {first.get('hashtags', [])}\n"
    )
    parts.append(meta_info)
    parts.append(f"TRANSCRIPT CHUNKS FOR VIDEO {label}:")
    
    for c in chunks:
        idx   = c.get("chunk_index", "?")
        score = c.get("score", 0.0)
        text  = c.get("text", "")
        parts.append(f"[Video {label}, chunk {idx}] (relevance={score:.3f}):\n{text}")
    return "\n\n".join(parts)


# helper to format message history for context window
def _format_history(memory: list[dict]) -> str:
    if not memory:
        return "No prior conversation."
    lines = []
    for turn in memory:
        role    = turn.get("role", "user").upper()
        content = turn.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


# loads/trims conversation history
async def load_memory_node(state: RAGState) -> dict:
    history = state.get("memory") or []
    trimmed = history[-(HISTORY_WINDOW * 2):]
    return {"memory": trimmed}


# encodes user question using embedder
async def embed_question_node(state: RAGState) -> dict:
    vector = await _embed_question(state["question"])
    return {"question_vector": vector}


# queries qdrant for video contexts
async def retrieve_parallel_node(state: RAGState) -> dict:
    job_id = state.get("job_id")
    results_a, results_b = await _search_both(
        state["question_vector"],
        k=RETRIEVAL_TOP_K,
        job_id=job_id if job_id != "test-job-001" else None,
    )
    return {"context_a": results_a, "context_b": results_b}


# feeds prompt to LLM and returns response with sources
async def generate_node(state: RAGState) -> dict:
    chunks_a = _format_chunks(state.get("context_a") or [], "A")
    chunks_b = _format_chunks(state.get("context_b") or [], "B")
    history  = _format_history(state.get("memory") or [])

    system_prompt = (
        "You are a video analytics expert helping content creators compare and improve their videos.\n\n"
        "You have access to transcript chunks and metadata for two videos:\n"
        "  - Video A (typically YouTube)\n"
        "  - Video B (typically Instagram Reels)\n\n"
        "RULES:\n"
        "1. Always cite sources inline as [Video A, chunk N] or [Video B, chunk N].\n"
        "2. Use engagement_rate from metadata (not from transcript text).\n"
        "   Formula: engagement_rate = (likes + comments) / views × 100\n"
        "3. Be specific and actionable — not generic advice.\n"
        "4. When comparing videos, structure your response clearly.\n"
        "5. If a question requires information not in the context, say so clearly."
    )

    user_content = (
        f"VIDEO A CONTEXT (cite as [Video A, chunk N]):\n"
        f"{chunks_a}\n\n"
        f"VIDEO B CONTEXT (cite as [Video B, chunk N]):\n"
        f"{chunks_b}\n\n"
        f"CONVERSATION HISTORY:\n"
        f"{history}\n\n"
        f"QUESTION: {state['question']}"
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    response = await _get_llm().ainvoke(messages)
    answer   = response.content

    retrieved_a = state.get("context_a") or []
    retrieved_b = state.get("context_b") or []
    sources = [
        {"video_id": c.get("video_id"), "chunk_index": c.get("chunk_index"), "score": round(c.get("score", 0.0), 4), "text": c.get("text", "")[:200]}
        for c in (retrieved_a + retrieved_b)
    ]

    memory = list(state.get("memory") or [])
    memory.append({"role": "user",      "content": state["question"]})
    memory.append({"role": "assistant", "content": answer})

    return {
        "answer":  answer,
        "sources": sources,
        "memory":  memory,
    }


# constructs state graph architecture
def _build_graph(checkpointer) -> object:
    builder = StateGraph(RAGState)

    builder.add_node("load_memory",    load_memory_node)
    builder.add_node("embed_question", embed_question_node)
    builder.add_node("retrieve",       retrieve_parallel_node)
    builder.add_node("generate",       generate_node)

    builder.add_edge(START,            "load_memory")
    builder.add_edge("load_memory",    "embed_question")
    builder.add_edge("embed_question", "retrieve")
    builder.add_edge("retrieve",       "generate")
    builder.add_edge("generate",       END)

    return builder.compile(checkpointer=checkpointer)


# compiles graph with in-memory checkpointer
def create_graph_no_memory() -> object:
    print("  [LLM] Creating graph with MemorySaver (in-process, test-safe)")
    return _build_graph(checkpointer=MemorySaver())


_saver_cm = None


# compiles graph with redis checkpointer
async def create_graph_with_redis() -> object:
    global _saver_cm
    from langgraph.checkpoint.redis.aio import AsyncRedisSaver

    print(f"  [LLM] Connecting to Redis at {REDIS_URL} for AsyncRedisSaver ...")
    _saver_cm = AsyncRedisSaver.from_conn_string(REDIS_URL)
    saver = await _saver_cm.__aenter__()
    try:
        await saver.asetup()
    except Exception:
        pass
    print("  [LLM] AsyncRedisSaver ready")
    return _build_graph(checkpointer=saver)


# compiles default graph trying redis first
async def create_graph() -> object:
    try:
        return await create_graph_with_redis()
    except Exception as e:
        print(f"  [LLM] Redis unavailable ({e}) — falling back to MemorySaver")
        return create_graph_no_memory()
