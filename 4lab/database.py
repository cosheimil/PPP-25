from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# URL для подключения к базе данных SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./library.db"

# Создаем движок SQLAlchemy
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Функция-генератор для получения сессии базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 
