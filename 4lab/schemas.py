from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import Annotated

class AuthorBase(BaseModel):
    """Базовая схема автора"""
    name: str

class AuthorCreate(AuthorBase):
    """Схема для создания автора"""
    pass

class Author(AuthorBase):
    """Схема для ответа с автором"""
    id: int

    class Config:
        from_attributes = True

class BookBase(BaseModel):
    """Базовая схема книги"""
    title: str
    year: int
    author_id: int

    @field_validator('year')
    def year_must_not_be_future(cls, v):
        """Проверка, что год издания не из будущего"""
        current_year = datetime.now().year
        if v > current_year:
            raise ValidationError(f'Год не может быть из будущего. Текущий год: {current_year}')
        return v

class BookCreate(BookBase):
    """Схема для создания книги"""
    pass

class Book(BookBase):
    """Схема для ответа с книгой"""
    id: int

    class Config:
        from_attributes = True 
