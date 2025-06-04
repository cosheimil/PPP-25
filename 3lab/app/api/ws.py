from typing import Dict, Any, Optional
import os
import json
import logging
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Query, HTTPException, status
from jose import jwt, JWTError
from celery.result import AsyncResult

from app.celery_worker import celery_app

router = APIRouter()
logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self, websocket: WebSocket, user_id: int):
        self.websocket = websocket
        self.user_id = user_id
        self.celery = celery_app

    async def handle_task_status(self, task_id: str) -> None:
        """Handle task status check request."""
        result = self.celery.AsyncResult(task_id)

        if result.successful():
            await self.send_success_response(task_id, result)
        elif result.state == "PROGRESS":
            await self.send_progress_response(task_id, result)
        else:
            await self.send_status_response(task_id, result.state)

    async def handle_search_request(self, data: Dict[str, Any]) -> None:
        """Handle new search request."""
        word = data.get("word")
        algorithm = data.get("algorithm")
        corpus_id = data.get("corpus_id")

        if not all(isinstance(x, str) for x in [word, algorithm]) or not isinstance(corpus_id, int):
            await self.send_error("Invalid search task format")
            return

        task = self.celery.send_task(
            "fuzzy_search_task",
            args=[word, algorithm, corpus_id]
        )

        await self.websocket.send_json({
            "status": "STARTED",
            "task_id": task.id,
            "word": word,
            "algorithm": algorithm
        })

    async def send_success_response(self, task_id: str, result: AsyncResult) -> None:
        """Send successful task completion response."""
        await self.websocket.send_json({
            "status": "COMPLETED",
            "task_id": task_id,
            "execution_time": result.result.get("execution_time"),
            "results": result.result.get("results")
        })

    async def send_progress_response(self, task_id: str, result: AsyncResult) -> None:
        """Send task progress response."""
        info = result.info or {}
        await self.websocket.send_json({
            "status": "PROGRESS",
            "task_id": task_id,
            "progress": info.get("progress", 0),
            "current_word": f"processing word {info.get('current_word', '?')}"
        })

    async def send_status_response(self, task_id: str, state: str) -> None:
        """Send task status response."""
        await self.websocket.send_json({
            "status": state,
            "task_id": task_id
        })

    async def send_error(self, message: str) -> None:
        """Send error message."""
        await self.websocket.send_json({"error": message})

def verify_token(token: str) -> Optional[int]:
    """Verify JWT token and return user_id."""
    try:
        payload = jwt.decode(
            token,
            os.getenv("SECRET_KEY"),
            algorithms=[os.getenv("ALGORITHM")]
        )
        return int(payload.get("sub"))
    except (JWTError, ValueError):
        return None

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
) -> None:
    """WebSocket endpoint for real-time task monitoring."""
    user_id = verify_token(token)
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    logger.info(f"WebSocket connected: user_id={user_id}")
    
    ws_manager = WebSocketManager(websocket, user_id)

    try:
        while True:
            try:
                data = await websocket.receive_text()
                parsed = json.loads(data)
            except json.JSONDecodeError:
                await ws_manager.send_error("Invalid JSON format")
                continue

            if isinstance(parsed, dict):
                if "task_id" in parsed and len(parsed) == 1:
                    task_id = parsed.get("task_id")
                    if not isinstance(task_id, str):
                        await ws_manager.send_error("Invalid task_id format")
                        continue
                    await ws_manager.handle_task_status(task_id)

                elif all(k in parsed for k in ("word", "algorithm", "corpus_id")):
                    await ws_manager.handle_search_request(parsed)

                else:
                    await ws_manager.send_error(
                        "Invalid message structure. Expected 'task_id' or {word, algorithm, corpus_id}."
                    )
            else:
                await ws_manager.send_error("Invalid message format")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: user_id={user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
