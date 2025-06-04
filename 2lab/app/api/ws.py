from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from sqlalchemy.orm import Session
from jose import jwt, JWTError
import os
from app.db.database import SessionLocal
from app.cruds import corpus as corpus_crud
from app.services import fuzzy_algorithms
from app.models.user import User

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_from_token(token: str, db: Session) -> User:
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError):
        return None
    return db.query(User).filter(User.id == user_id).first()

@router.websocket("/ws/search")
async def websocket_search(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    user = get_user_from_token(token, db)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            word = data.get("word")
            algorithm = data.get("algorithm")
            corpus_id = data.get("corpus_id")

            if not all([word, algorithm, corpus_id]):
                await websocket.send_json({"error": "Missing parameters"})
                continue

            corpus = corpus_crud.get_corpus_by_id(db, corpus_id)
            if not corpus:
                await websocket.send_json({"error": "Corpus not found"})
                continue

            result = fuzzy_algorithms.search(word, corpus.text, algorithm)
            await websocket.send_json(result)

    except WebSocketDisconnect:
        print("WebSocket disconnected")
