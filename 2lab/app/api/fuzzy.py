from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.schemas.corpus import (
    CorpusCreate, CorpusOut, CorpusListOut, SearchRequest, SearchResponse
)
from app.cruds import corpus as corpus_crud
from app.services import fuzzy_algorithms
from app.core.deps import get_db, get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/upload_corpus", response_model=CorpusOut)
def upload_corpus(
    data: CorpusCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return corpus_crud.create_corpus(db, data)

@router.get("/corpuses", response_model=CorpusListOut)
def get_corpuses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    corpuses = corpus_crud.get_corpuses(db)
    return {"corpuses": corpuses}

@router.post("/search_algorithm", response_model=SearchResponse)
def search(
    request: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    corpus = corpus_crud.get_corpus_by_id(db, request.corpus_id)
    if not corpus:
        raise HTTPException(status_code=404, detail="Corpus not found")

    result = fuzzy_algorithms.search(
        word=request.word,
        corpus=corpus.text,
        algorithm=request.algorithm
    )
    return result
