# Fuzzy Search API

Проект для выполнения лабораторной работы по нечеткому поиску. Реализовано REST API и WebSocket взаимодействие с поддержкой Celery и Redis для асинхронной обработки задач.

---

## Стек технологий

- Python 3.10+
- FastAPI
- SQLAlchemy
- Alembic
- Celery
- Redis
- Pydantic
- WebSocket
- Uvicorn

---

## Быстрый старт

### 1. Клонируем проект
```bash
git clone <репозиторий>
cd <название_проекта>
```

### 2. Устанавливаем зависимости
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### 3. Инициализируем базу данных
```bash
alembic upgrade head
```

### 4. Запускаем FastAPI сервер
```bash
python main.py
```

Сервер будет доступен по адресу: `http://127.0.0.1:8000`

Документация к API методам доступна по адресу: `http://127.0.0.1:8000/docs`

---

## Запуск Celery (обязательно для async-функций)

Убеждаемся, что Redis запущен:

```bash
redis-server
```

В другом терминале запускаем Celery:

```bash
celery -A app.celery_worker worker --loglevel=info --pool=solo
```

---

## 🗃Структура проекта

```
├── app/
│   ├── api/              # Роутеры (HTTP + WebSocket)
│   ├── core/             # Авторизация и зависимости
│   ├── cruds/            # Работа с БД
│   ├── db/               # SQLAlchemy и Alembic
│   ├── models/           # Pydantic + SQLAlchemy модели
│   ├── schemas/          # Схемы запроса/ответа
│   ├── services/         # Реализация алгоритмов
│   ├── celery_worker.py  # Запуск Celery
│   └── celeryconfig.py   # Конфигурация Celery
├── .env
├── .gitignore
├── main.py               # Точка входа
├── alembic.ini
├── requirements.txt
└── README.md
```

---

## Как протестировать API (Postman)

### 1. Регистрация
```
POST /auth/sign-up
```
```json
{
  "email": "test@example.com",
  "password": "123456"
}
```

### 2. Авторизация
```
POST /auth/login
```

Получите `token` и добавьте его во все запросы:
```
Authorization: Bearer <ваш токен>
```

---

### 3. Загрузка корпуса
```
POST /fuzzy/upload_corpus
```
```json
{
  "corpus_name": "Tech Terms",
  "text": "python pythons pithon pytorch numpy pandas pipeline parameter parse"
}
```

### 4. Поиск (синхронно)
```
POST /fuzzy/search_algorithm
```
```json
{
  "word": "python",
  "algorithm": "levenshtein",
  "corpus_id": 1
}
```

### 5. Поиск (асинхронно через Celery)
```
POST /fuzzy/async_search
```
```json
{
  "word": "python",
  "algorithm": "ngram",
  "corpus_id": 1
}
```

Ответ:
```json
{
  "task_id": "abc123..."
}
```

Потом:
```
GET /fuzzy/task_status?task_id=abc123...
```

---

## Тест WebSocket

Используем любой клиент WebSocket (например, https://www.piesocket.com/websocket-tester, либо внутри Postman)

Подключение:

```
ws://localhost:8000/ws/search?token=<токен>
```

После подключения отправляем JSON:

```json
{
  "word": "example",
  "algorithm": "ngram",
  "corpus_id": 1
}
```

Получишь:
```json
{
  "execution_time": 0.0013,
  "results": [...]
}
```

---

## Объяснение алгоритмов

### Левенштейн (Levenshtein)
Считает, сколько правок нужно, чтобы превратить одно слово в другое (вставка, удаление, замена символа).

Пример: `"cat"` → `"cut"` = 1 правка

---

### N-граммы
Разбивает слова на кусочки (например, по 2 буквы), и сравнивает, сколько из них совпадает.

Пример: `"example"` → `['ex', 'xa', 'am', 'mp', 'pl', 'le']`

---

## Очистка базы

Удалить файл базы:
```bash
rm fuzzy.db
```

Пересоздать:
```bash
alembic upgrade head
```