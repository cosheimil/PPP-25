import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

class Config:
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", 9000))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
    INFO_FORMAT = os.getenv("PROCESS_INFO_FORMAT", "json")  # or 'xml'
