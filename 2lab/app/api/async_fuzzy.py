from fastapi import APIRouter, Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.schemas.corpus import SearchRequest
from celery.result import AsyncResult
from app.celery_worker import fuzzy_search_task
from app.core.deps import get_db, get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/async_search")
def start_search_task(
    request: SearchRequest,
    current_user: User = Depends(get_current_user)
):
    task = fuzzy_search_task.delay(request.word, request.algorithm, request.corpus_id)
    return {"task_id": task.id}

@router.get("/task_status")
def get_task_status(task_id: str, current_user: User = Depends(get_current_user)):
    try:
        result = AsyncResult(task_id)
        status = result.status  # тут может упасть, если backend не работает
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch task status: {str(e)}")

    return {
        "status": status,
        "progress": 100 if result.successful() else 0,
        "result": result.result if result.ready() else None
    }
