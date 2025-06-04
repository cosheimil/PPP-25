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

## Установка и настройка

### 1. Установка Redis
```bash
# Установка Redis сервера и клиента
sudo apt install redis-server redis-tools -y

# Запуск Redis сервера
sudo systemctl start redis-server

# Проверка работоспособности Redis
redis-cli ping  # Должен ответить: PONG
```

### 2. Настройка виртуального окружения
```bash
# Создание виртуального окружения
python -m venv .venv

# Активация виртуального окружения
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt
```

### 3. Запуск компонентов системы

#### Запуск Redis (если не запущен через systemd)
```bash
redis-server
```

#### Запуск Celery Worker (в отдельном терминале)
```bash
# Активируйте виртуальное окружение и выполните:
celery -A app.celery_worker worker --loglevel=info --pool=solo
```

#### Запуск FastAPI сервера
```bash
# Активируйте виртуальное окружение и выполните:
python main.py
```

После запуска всех компонентов:
- FastAPI сервер будет доступен по адресу: http://127.0.0.1:8000
- Swagger UI (документация API): http://127.0.0.1:8000/docs

---

## Тестирование API

### 1. Регистрация пользователя
```bash
curl -X POST "http://127.0.0.1:8000/auth/sign-up" \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"123456"}'
```

### 2. Авторизация и получение токена
```bash
curl -X POST "http://127.0.0.1:8000/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username":"test@example.com","password":"123456"}'
```

### 3. Загрузка корпуса текстов
```bash
curl -X POST "http://127.0.0.1:8000/fuzzy/upload_corpus" \
     -H "Authorization: Bearer <ваш_токен>" \
     -H "Content-Type: application/json" \
     -d '{"corpus_name":"Tech Terms","text":"python pythons pithon pytorch numpy pandas pipeline parameter parse"}'
```

### 4. Синхронный поиск
```bash
curl -X POST "http://127.0.0.1:8000/fuzzy/search_algorithm" \
     -H "Authorization: Bearer <ваш_токен>" \
     -H "Content-Type: application/json" \
     -d '{"word":"python","algorithm":"levenshtein","corpus_id":1}'
```

### 5. Асинхронный поиск через Celery
```bash
curl -X POST "http://127.0.0.1:8000/fuzzy/async_search" \
     -H "Authorization: Bearer <ваш_токен>" \
     -H "Content-Type: application/json" \
     -d '{"word":"python","algorithm":"ngram","corpus_id":1}'
```

### 6. Проверка статуса асинхронной задачи
```bash
curl "http://127.0.0.1:8000/fuzzy/task_status?task_id=<id_задачи>" \
     -H "Authorization: Bearer <ваш_токен>"
```

## WebSocket подключение

Для тестирования WebSocket можно использовать любой WebSocket клиент (например, websocat):

```bash
# Установка websocat
cargo install websocat

# Подключение к WebSocket серверу
websocat "ws://localhost:8000/ws/search?token=<ваш_токен>"

# После подключения отправьте JSON:
{"word":"python","algorithm":"ngram","corpus_id":1}
```

---

## Объяснение алгоритмов

### Левенштейн (Levenshtein)
Считает, сколько правок нужно, чтобы превратить одно слово в другое (вставка, удаление, замена символа).

Пример: `"cat"` → `"cut"` = 1 правка

### N-граммы
Разбивает слова на кусочки (например, по 2 буквы), и сравнивает, сколько из них совпадает.

Пример: `"example"` → `['ex', 'xa', 'am', 'mp', 'pl', 'le']`

---

## Диагностика проблем

### Проверка состояния сервисов

1. Проверка Redis:
```bash
redis-cli ping  # Должен ответить: PONG
```

2. Проверка Celery:
```bash
celery -A app.celery_worker status
```

3. Проверка FastAPI:
```bash
curl http://127.0.0.1:8000/docs  # Должен открыться Swagger UI
```

### Очистка данных

Если нужно очистить базу данных:
```bash
rm fuzzy.db
```

### Логи

- FastAPI логи выводятся в консоль при запуске сервера
- Celery логи можно увидеть в терминале с запущенным worker
- Redis логи: `sudo journalctl -u redis-server`
