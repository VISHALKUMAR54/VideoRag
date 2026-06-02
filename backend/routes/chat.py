import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from models import ChatRequest

router = APIRouter(tags=["chat"])

_rag_graph = None


# load RAG graph on first chat request
async def _get_graph():
    global _rag_graph
    if _rag_graph is None:
        from services.llm import create_graph
        _rag_graph = await create_graph()
    return _rag_graph


# stream LLM response tokens as Server-Sent Events
@router.post("/chat")
async def chat(req: ChatRequest) -> StreamingResponse:
    graph = await _get_graph()

    async def token_stream():
        try:
            async for token in graph.astream(
                {"question": req.question, "job_id": req.job_id},
                config={"configurable": {"thread_id": req.thread_id}},
                stream_mode="messages",
            ):
                if token and hasattr(token[0], "content") and token[0].content:
                    content = token[0].content.replace("\n", "\\n")
                    yield f"data: {content}\n\n"
        except Exception as e:
            error_payload = json.dumps({"error": str(e)})
            yield f"data: [ERROR] {error_payload}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        token_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":       "keep-alive",
        },
    )
