from fastapi import FastAPI, HTTPException, Depends, Response, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import ValidationError

import models
import schemas
import database
from database import engine, get_db

# Создаем таблицы в базе данных
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/authors", response_model=List[schemas.Author])
def get_authors(db: Session = Depends(get_db)):
    """Получение списка всех авторов"""
    return db.query(models.Author).all()

@app.post("/authors", response_model=schemas.Author, status_code=201)
def create_author(author: schemas.AuthorCreate, db: Session = Depends(get_db)):
    """Создание нового автора"""
    db_author = models.Author(**author.model_dump())
    db.add(db_author)
    db.commit()
    db.refresh(db_author)
    return db_author

@app.get("/authors/{author_id}", response_model=schemas.Author)
def get_author(author_id: int, db: Session = Depends(get_db)):
    """Получение автора по ID"""
    author = db.query(models.Author).filter(models.Author.id == author_id).first()
    if author is None:
        raise HTTPException(status_code=404, detail="Автор не найден")
    return author

@app.put("/authors/{author_id}", response_model=schemas.Author)
def update_author(author_id: int, author: schemas.AuthorCreate, db: Session = Depends(get_db)):
    """Обновление данных автора"""
    db_author = db.query(models.Author).filter(models.Author.id == author_id).first()
    if db_author is None:
        raise HTTPException(status_code=404, detail="Автор не найден")
    
    for key, value in author.model_dump().items():
        setattr(db_author, key, value)
    
    db.commit()
    db.refresh(db_author)
    return db_author

@app.delete("/authors/{author_id}", status_code=204)
def delete_author(author_id: int, db: Session = Depends(get_db)):
    """Удаление автора и всех его книг"""
    author = db.query(models.Author).filter(models.Author.id == author_id).first()
    if author is None:
        raise HTTPException(status_code=404, detail="Автор не найден")
    
    db.delete(author)
    db.commit()
    return Response(status_code=204)

@app.get("/books", response_model=List[schemas.Book])
def get_books(author_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Получение списка книг с опциональной фильтрацией по автору"""
    query = db.query(models.Book)
    if author_id is not None:
        query = query.filter(models.Book.author_id == author_id)
    return query.all()

@app.post("/books", response_model=schemas.Book, status_code=201)
async def create_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    """Создание новой книги"""
    try:
        # Проверка года издания
        current_year = datetime.now().year
        if book.year > current_year:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Год не может быть из будущего. Текущий год: {current_year}"
            )
        
        # Проверка существования автора
        author = db.query(models.Author).filter(models.Author.id == book.author_id).first()
        if author is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Автор не найден"
            )
        
        db_book = models.Book(**book.model_dump())
        db.add(db_book)
        db.commit()
        db.refresh(db_book)
        return db_book
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
