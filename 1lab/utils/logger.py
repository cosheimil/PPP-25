import logging
from utils.config import Config

def setup_logger(name: str) -> logging.Logger:
    # Создаёт и настраивает логгер
    logger = logging.getLogger(name)
    logger.setLevel(Config.LOG_LEVEL)

    ch = logging.StreamHandler()
    ch.setLevel(Config.LOG_LEVEL)

    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    ch.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(ch)

    return logger
