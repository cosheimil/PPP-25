import time
from celery import Celery
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.cruds import corpus as corpus_crud
from app.services import fuzzy_algorithms

celery_app = Celery("tasks")
celery_app.config_from_object("app.celeryconfig")

@celery_app.task(name="fuzzy_search_task", bind=True)
def fuzzy_search_task(self, word: str, algorithm: str, corpus_id: int):
    db: Session = SessionLocal()
    corpus = corpus_crud.get_corpus_by_id(db, corpus_id)
    if not corpus:
        return {"error": "Corpus not found"}

    words = list(set(corpus.text.split()))
    total = len(words)

    start_time = time.time()

    results = []
    for idx, w in enumerate(words):
        if algorithm == "levenshtein":
            distance = fuzzy_algorithms.levenshtein_distance(word, w)
        elif algorithm == "ngram":
            distance = round(fuzzy_algorithms.ngram_similarity(word, w) * 10)
        else:
            continue

        self.update_state(
            state='PROGRESS',
            meta={
                'progress': int((idx + 1) / total * 100),
                'current_word': f'{idx + 1}/{total}'
            }
        )

        results.append({"word": w, "distance": distance})

    sorted_results = sorted(results, key=lambda x: x["distance"])[:10]
    end_time = time.time()

    return {
        "execution_time": round(end_time - start_time, 4),
        "results": sorted_results
    }
