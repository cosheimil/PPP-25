from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Author(Base):
    """Модель автора книги"""
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    # Связь один-ко-многим с книгами, каскадное удаление
    books = relationship("Book", back_populates="author", cascade="all, delete")

class Book(Base):
    """Модель книги"""
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    author_id = Column(Integer, ForeignKey("authors.id", ondelete="CASCADE"), nullable=False)
    # Связь с автором
    author = relationship("Author", back_populates="books") 
