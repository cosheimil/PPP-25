from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
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

@router.post(
    "/upload_corpus",
    response_model=CorpusOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload new corpus",
    description="Upload a new text corpus for fuzzy search"
)
async def upload_corpus(
    data: CorpusCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CorpusOut:
    """
    Upload a new corpus with the following information:
    - **name**: unique name for the corpus
    - **text**: text content of the corpus
    """
    return corpus_crud.create_corpus(db, data)

@router.get(
    "/corpuses",
    response_model=CorpusListOut,
    summary="Get all corpuses",
    description="Get a list of all available text corpuses"
)
async def get_corpuses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CorpusListOut:
    """
    Retrieve all available text corpuses.
    """
    corpuses = corpus_crud.get_corpuses(db)
    return CorpusListOut(corpuses=corpuses)

@router.post(
    "/search_algorithm",
    response_model=SearchResponse,
    summary="Perform fuzzy search",
    description="Search for a word in a corpus using specified algorithm"
)
async def search(
    request: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SearchResponse:
    """
    Perform fuzzy search with the following parameters:
    - **word**: word to search for
    - **algorithm**: fuzzy search algorithm (levenshtein/ngram)
    - **corpus_id**: ID of the corpus to search in
    """
    corpus = corpus_crud.get_corpus_by_id(db, request.corpus_id)
    if not corpus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corpus not found"
        )

    return fuzzy_algorithms.search(
        word=request.word,
        corpus=corpus.text,
        algorithm=request.algorithm
    )
