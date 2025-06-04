from celery import Celery
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.cruds import corpus as corpus_crud
from app.services import fuzzy_algorithms

celery_app = Celery("tasks")

celery_app.config_from_object("app.celeryconfig")

@celery_app.task(name="fuzzy_search_task")
def fuzzy_search_task(word: str, algorithm: str, corpus_id: int):
    db: Session = SessionLocal()
    corpus = corpus_crud.get_corpus_by_id(db, corpus_id)
    if not corpus:
        return {"error": "Corpus not found"}
    result = fuzzy_algorithms.search(word, corpus.text, algorithm)
    return result
