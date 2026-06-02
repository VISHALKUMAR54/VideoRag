import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from state import get_redis

router = APIRouter(tags=["websocket"])


# push ingestion events to the client in real-time
@router.websocket("/ws/{job_id}")
async def websocket_status(websocket: WebSocket, job_id: str) -> None:
    await websocket.accept()
    print(f"  [WS] Client connected for job_id={job_id}")

    r      = get_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe(f"ws:{job_id}")

    try:
        async for message in pubsub.listen():
            if message.get("type") == "message":
                data = message.get("data", "")
                await websocket.send_text(data)
                print(f"  [WS] Pushed to client: {data}")
    except WebSocketDisconnect:
        print(f"  [WS] Client disconnected for job_id={job_id}")
    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.unsubscribe(f"ws:{job_id}")
        await pubsub.aclose()
        print(f"  [WS] Cleaned up pub/sub for job_id={job_id}")
